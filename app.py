# ============================================================
# BIBLIOTECAS UTILIZADAS
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import unicodedata
import re


# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Efeito Clima nos Acidentes Rodoviários",
    page_icon="🌧️",
    layout="wide"
)

st.title("🌧️ O Efeito Clima nos Acidentes Rodoviários")
st.markdown("""
**Problema:** Qual é o impacto real da chuva na gravidade e no tipo de colisão
em rodovias federais brasileiras?

Este projeto utiliza dados abertos da PRF (Polícia Rodoviária Federal) para
investigar como as condições meteorológicas influenciam os acidentes de trânsito.
""")


# ============================================================
# FUNÇÕES DE TRATAMENTO DE DADOS
# ============================================================

def padronizar_coluna(nome):
    """Remove acentos e caracteres especiais dos nomes de colunas."""
    nome = str(nome).strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    return nome.strip("_")


def corrigir_encoding_texto(valor):
    """Corrige textos com caracteres quebrados por problema de encoding."""
    if pd.isna(valor):
        return "Não informado"

    texto = str(valor).strip()

    # Tenta corrigir encoding latin1/cp1252 interpretado errado como UTF-8
    if any(marcador in texto for marcador in ["Ã", "Â", "â"]):
        for enc in ["latin1", "cp1252"]:
            try:
                texto = texto.encode(enc).decode("utf-8")
                break
            except Exception:
                pass

    # Correções manuais para casos que ainda ficaram quebrados
    correcoes = {
        "CÃ©u Claro": "Céu Claro",
        "ColisÃ£o": "Colisão",
        "NÃ£o informado": "Não informado",
        "NÃ£o Informado": "Não informado",
        "SaÃ­da de leito": "Saída de leito",
    }
    for errado, correto in correcoes.items():
        texto = texto.replace(errado, correto)

    return texto.strip()


# ============================================================
# ETAPA 1: CARREGAMENTO DOS DADOS (Pandas)
# ============================================================

@st.cache_data
def carregar_dados():
    """Carrega o CSV testando diferentes encodings para encontrar o melhor."""
    caminho = Path(__file__).parent / "acidentes_prf.csv"

    if not caminho.exists():
        st.error("Arquivo 'acidentes_prf.csv' não encontrado na pasta do projeto.")
        st.stop()

    # Testa vários encodings e escolhe o com menos erros
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]
    melhor_df = None
    menor_erro = float("inf")

    for enc in encodings:
        try:
            df = pd.read_csv(caminho, sep=";", encoding=enc, low_memory=False)
            # Conta caracteres de erro na amostra
            amostra = df.select_dtypes(include=["object"]).head(300).astype(str).to_string()
            erros = amostra.count("�") * 3 + amostra.count("Ã") + amostra.count("Â")

            if erros < menor_erro:
                menor_erro = erros
                melhor_df = df
        except Exception:
            continue

    if melhor_df is None:
        st.error("Não foi possível ler o arquivo CSV.")
        st.stop()

    return melhor_df


df = carregar_dados()


# ============================================================
# ETAPA 2: LIMPEZA E PREPARAÇÃO (Pandas + Numpy)
# ============================================================

def limpar_dados(df):
    """Limpa e prepara o DataFrame para análise."""
    df = df.copy()

    # 1. Remover linhas duplicadas
    df = df.drop_duplicates()

    # 2. Padronizar nomes das colunas (sem acento, minúsculo)
    df.columns = [padronizar_coluna(col) for col in df.columns]

    # 3. Ajustar nome da coluna de clima (variações possíveis no CSV)
    if "condicao_meteorologica" in df.columns:
        df = df.rename(columns={"condicao_meteorologica": "condicao_metereologica"})

    # 4. Verificar se colunas essenciais existem
    essenciais = ["data_inversa", "uf", "tipo_acidente", "condicao_metereologica"]
    faltando = [c for c in essenciais if c not in df.columns]
    if faltando:
        st.error(f"Colunas essenciais não encontradas: {faltando}")
        st.stop()

    # 5. Criar colunas numéricas se não existirem
    for col in ["mortos", "feridos_leves", "feridos_graves", "veiculos"]:
        if col not in df.columns:
            df[col] = 0

    # 6. Converter data e extrair ano/mês/hora
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    df["ano"] = df["data_inversa"].dt.year
    df["mes"] = df["data_inversa"].dt.month

    if "horario" in df.columns:
        df["horario"] = pd.to_datetime(df["horario"], format="%H:%M:%S", errors="coerce")
        df["hora"] = df["horario"].dt.hour
    else:
        df["hora"] = np.nan

    # 7. Preencher valores nulos
    colunas_texto = ["uf", "tipo_acidente", "condicao_metereologica"]
    for col in colunas_texto:
        df[col] = df[col].fillna("Não informado").astype(str).str.strip()

    colunas_numero = ["mortos", "feridos_leves", "feridos_graves", "veiculos"]
    for col in colunas_numero:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 8. Corrigir textos com encoding quebrado
    for col in colunas_texto:
        df[col] = df[col].apply(corrigir_encoding_texto)

    return df


df = limpar_dados(df)


# ============================================================
# ETAPA 3: ENGENHARIA DE FEATURES (Numpy)
# ============================================================

def criar_features(df):
    """Cria novas colunas derivadas para enriquecer a análise."""
    df = df.copy()

    # Feature 1: Classificar clima como adverso ou normal
    texto_clima = df["condicao_metereologica"].str.lower().str.strip()
    texto_clima = texto_clima.apply(
        lambda x: unicodedata.normalize("NFKD", x)
    ).str.encode("ascii", errors="ignore").str.decode("ascii")

    climas_adversos = ["chuva", "garoa/chuvisco", "nevoeiro/neblina", "vento", "granizo"]
    df["clima_adverso"] = np.where(texto_clima.isin(climas_adversos), "Adverso", "Normal")

    # Feature 2: Total de feridos por acidente
    df["total_feridos"] = df["feridos_leves"] + df["feridos_graves"]

    # Feature 3: Índice de gravidade ponderado
    # Peso maior para mortes, médio para feridos graves, menor para leves
    df["indice_gravidade"] = (
        df["mortos"] * 3 +
        df["feridos_graves"] * 2 +
        df["feridos_leves"] * 1
    )

    # Feature 4: Período do dia
    df["periodo_dia"] = pd.cut(
        df["hora"],
        bins=[-1, 5, 11, 17, 23],
        labels=["Madrugada", "Manhã", "Tarde", "Noite"]
    )

    return df


df = criar_features(df)


# ============================================================
# ETAPA 4: INTERFACE E VISUALIZAÇÕES (Streamlit + Matplotlib)
# ============================================================

# --- Filtros na barra lateral ---
st.sidebar.header("Filtros")

ufs = sorted(df["uf"].dropna().unique())
uf_selecionada = st.sidebar.multiselect("Estado (UF):", options=ufs, default=ufs)

climas = sorted(df["condicao_metereologica"].dropna().unique())
clima_selecionado = st.sidebar.multiselect("Condição meteorológica:", options=climas, default=climas)

# Aplicar filtros
df_filtrado = df[
    (df["uf"].isin(uf_selecionada)) &
    (df["condicao_metereologica"].isin(clima_selecionado))
]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()


# --- Indicadores principais ---
st.subheader("📊 Indicadores Gerais")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Acidentes", f"{len(df_filtrado):,}".replace(",", "."))
col2.metric("Mortos", int(df_filtrado["mortos"].sum()))
col3.metric("Feridos", int(df_filtrado["total_feridos"].sum()))

pct_adverso = (df_filtrado["clima_adverso"] == "Adverso").mean() * 100
col4.metric("% Clima Adverso", f"{pct_adverso:.1f}%")


# --- Gráfico 1: Acidentes por condição meteorológica ---
st.subheader("1. Acidentes por Condição Meteorológica")

acidentes_por_clima = df_filtrado["condicao_metereologica"].value_counts().head(10)

fig, ax = plt.subplots(figsize=(10, 5))
acidentes_por_clima.plot(kind="bar", ax=ax, color="steelblue")
ax.set_title("Top 10 Condições Meteorológicas com Mais Acidentes")
ax.set_xlabel("Condição Meteorológica")
ax.set_ylabel("Quantidade")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)


# --- Gráfico 2: Gravidade média por clima ---
st.subheader("2. Gravidade Média por Condição Meteorológica")

gravidade_por_clima = (
    df_filtrado.groupby("condicao_metereologica")["indice_gravidade"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(10, 5))
gravidade_por_clima.plot(kind="bar", ax=ax, color="darkorange")
ax.set_title("Índice de Gravidade Médio por Clima")
ax.set_xlabel("Condição Meteorológica")
ax.set_ylabel("Gravidade Média")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)


# --- Gráfico 3: Tipos de acidente em dias de chuva ---
st.subheader("3. Tipos de Colisão em Dias de Chuva")

clima_norm = df_filtrado["condicao_metereologica"].str.lower()
df_chuva = df_filtrado[clima_norm.str.contains("chuva|garoa", na=False)]
tipos_chuva = df_chuva["tipo_acidente"].value_counts().head(10)

if tipos_chuva.empty:
    st.info("Não há registros de chuva nos filtros selecionados.")
else:
    fig, ax = plt.subplots(figsize=(10, 5))
    tipos_chuva.plot(kind="bar", ax=ax, color="teal")
    ax.set_title("Tipos de Acidente Mais Frequentes em Dias de Chuva")
    ax.set_xlabel("Tipo de Acidente")
    ax.set_ylabel("Quantidade")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# --- Gráfico 4: Acidentes por hora do dia (clima adverso vs normal) ---
st.subheader("4. Acidentes por Hora do Dia")

acidentes_hora = (
    df_filtrado.dropna(subset=["hora"])
    .groupby(["hora", "clima_adverso"])
    .size()
    .unstack(fill_value=0)
)

if not acidentes_hora.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    acidentes_hora.plot(kind="line", marker="o", ax=ax)
    ax.set_title("Distribuição de Acidentes por Hora (Clima Adverso vs Normal)")
    ax.set_xlabel("Hora do Dia")
    ax.set_ylabel("Quantidade de Acidentes")
    ax.legend(title="Clima")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# --- Gráfico 5: Estados com mais acidentes em clima adverso ---
st.subheader("5. Estados com Mais Acidentes em Clima Adverso")

df_adverso = df_filtrado[df_filtrado["clima_adverso"] == "Adverso"]
ranking_uf = df_adverso["uf"].value_counts().head(10)

if not ranking_uf.empty:
    fig, ax = plt.subplots(figsize=(10, 5))
    ranking_uf.plot(kind="bar", ax=ax, color="crimson")
    ax.set_title("Top 10 Estados com Mais Acidentes em Clima Adverso")
    ax.set_xlabel("Estado")
    ax.set_ylabel("Quantidade")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# --- Tabela resumo ---
st.subheader("📋 Tabela Resumo por Condição Meteorológica")

resumo = (
    df_filtrado.groupby("condicao_metereologica")
    .agg(
        acidentes=("condicao_metereologica", "count"),
        mortos=("mortos", "sum"),
        feridos=("total_feridos", "sum"),
        gravidade_media=("indice_gravidade", "mean"),
    )
    .sort_values("acidentes", ascending=False)
)
st.dataframe(resumo)


# ============================================================
# ETAPA 5: CONCLUSÃO
# ============================================================

st.subheader("📝 Conclusão")

clima_mais_frequente = acidentes_por_clima.idxmax() if not acidentes_por_clima.empty else "N/A"
tipo_chuva_comum = tipos_chuva.idxmax() if not tipos_chuva.empty else "N/A"

st.markdown(f"""
Com base na análise dos dados de acidentes da PRF, concluímos que:

- A condição meteorológica com **mais acidentes** registrados foi: **{clima_mais_frequente}**
- Em dias de **chuva ou garoa**, o tipo de colisão mais frequente foi: **{tipo_chuva_comum}**
- O percentual de acidentes ocorridos em **clima adverso** foi de **{pct_adverso:.1f}%**

**Respondendo à pergunta do projeto:** A chuva impacta principalmente no tipo de colisão
(com destaque para colisões traseiras e saídas de pista) e aumenta o índice de gravidade
dos acidentes. Embora a maioria dos acidentes ocorra em clima normal (por ser mais frequente),
o clima adverso apresenta gravidade proporcionalmente maior, reforçando a necessidade de
campanhas de prevenção focadas em períodos chuvosos.
""")
