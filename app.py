import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import unicodedata
import re

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix


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
Este projeto analisa como as condições meteorológicas influenciam a frequência,
o tipo e a gravidade dos acidentes em rodovias federais brasileiras.
""")


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalizar_nome_coluna(nome):
    """
    Padroniza nomes de colunas:
    - remove espaços;
    - deixa minúsculo;
    - remove acentos;
    - troca caracteres especiais por underline.
    """
    nome = str(nome).strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    nome = nome.strip("_")
    return nome


def normalizar_texto_comparacao(texto):
    """
    Cria uma versão sem acento e minúscula para comparações internas.
    Exemplo: 'Céu Claro' -> 'ceu claro'
    """
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


def corrigir_valor_texto(valor):
    if pd.isna(valor):
        return "Não informado"

    texto = str(valor).strip()

    # Tenta corrigir casos como CÃ©u, ColisÃ£o, SaÃ­da
    if any(marcador in texto for marcador in ["Ã", "Â", "â"]):
        for encoding in ["latin1", "cp1252"]:
            try:
                texto = texto.encode(encoding).decode("utf-8")
                break
            except Exception:
                pass

    # Correções diretas
    substituicoes = {
        "C�u Claro": "Céu Claro",
        "Cï¿½u Claro": "Céu Claro",
        "CÃ©u Claro": "Céu Claro",

        "Sa�da de leito carro��vel": "Saída de leito carroçável",
        "Saï¿½da de leito carroï¿½ï¿½vel": "Saída de leito carroçável",
        "SaÃ­da de leito carroÃ§Ã¡vel": "Saída de leito carroçável",

        "Colis�o": "Colisão",
        "Colisï¿½o": "Colisão",
        "ColisÃ£o": "Colisão",

        "N�o informado": "Não informado",
        "N�o Informado": "Não informado",
        "Nï¿½o informado": "Não informado",
        "Nï¿½o Informado": "Não informado",
        "NÃ£o informado": "Não informado",
        "NÃ£o Informado": "Não informado",

        "Contram�o": "Contramão",
        "Contramï¿½o": "Contramão",
        "ContramÃ£o": "Contramão",

        "Interse��o": "Interseção",
        "Interseï¿½ï¿½o": "Interseção",
        "InterseÃ§Ã£o": "Interseção",

        "Sinaliza��o": "Sinalização",
        "Sinalizaï¿½ï¿½o": "Sinalização",
        "SinalizaÃ§Ã£o": "Sinalização",
    }

    for errado, correto in substituicoes.items():
        texto = texto.replace(errado, correto)

    # Correções por padrão para qualquer palavra que ainda tenha � no meio
    texto = re.sub(r"C.+u Claro", "Céu Claro", texto)
    texto = re.sub(r"Sa.+da de leito carro.+vel", "Saída de leito carroçável", texto)
    texto = re.sub(r"Colis.+o", "Colisão", texto)
    texto = re.sub(r"Contram.+o", "Contramão", texto)
    texto = re.sub(r"Interse.+o", "Interseção", texto)
    texto = re.sub(r"Sinaliza.+o", "Sinalização", texto)
    texto = re.sub(r"N.+o informado", "Não informado", texto, flags=re.IGNORECASE)

    # Ajustes finais para frases que aparecem nos filtros
    texto = texto.replace("Colisão com objeto", "Colisão com objeto")
    texto = texto.replace("Colisão traseira", "Colisão traseira")
    texto = texto.replace("Colisão frontal", "Colisão frontal")
    texto = texto.replace("Colisão lateral", "Colisão lateral")

    return texto.strip()


def corrigir_textos_dataframe(df):
    """
    Aplica correção de texto em todas as colunas textuais.
    """
    df = df.copy()

    colunas_texto = df.select_dtypes(include=["object"]).columns

    for coluna in colunas_texto:
        df[coluna] = df[coluna].apply(corrigir_valor_texto)

    return df


# ============================================================
# CARREGAMENTO DOS DADOS
# ============================================================

@st.cache_data
def carregar_dados():
    caminho_arquivo = Path(__file__).parent / "acidentes_prf.csv"

    if not caminho_arquivo.exists():
        st.error("Arquivo 'acidentes_prf.csv' não encontrado.")
        st.warning("""
        Coloque o arquivo CSV dentro da mesma pasta do app.py.

        A pasta deve conter:
        - app.py
        - acidentes_prf.csv
        """)
        st.stop()

    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1"]

    melhor_df = None
    melhor_encoding = None
    menor_erro = float("inf")

    for encoding in encodings:
        try:
            df_teste = pd.read_csv(
                caminho_arquivo,
                sep=";",
                encoding=encoding,
                low_memory=False
            )

            amostra_texto = (
                df_teste
                .select_dtypes(include=["object"])
                .head(500)
                .astype(str)
                .to_string()
            )

            erros_codificacao = (
                amostra_texto.count(" ") * 3 +
                amostra_texto.count("ï¿½") * 5 +
                amostra_texto.count("Ã") +
                amostra_texto.count("Â")
            )

            if erros_codificacao < menor_erro:
                menor_erro = erros_codificacao
                melhor_df = df_teste
                melhor_encoding = encoding

        except UnicodeDecodeError:
            continue
        except Exception:
            continue

    if melhor_df is None:
        st.error("Não foi possível ler o arquivo CSV.")
        st.stop()

    return melhor_df, melhor_encoding


df, encoding_usado = carregar_dados()

st.caption(f"Arquivo carregado com encoding: {encoding_usado}")


# ============================================================
# LIMPEZA DOS DADOS
# ============================================================

def limpar_dados(df):
    df = df.copy()

    # Remover duplicatas
    df = df.drop_duplicates()

    # Padronizar nomes das colunas
    df.columns = [normalizar_nome_coluna(coluna) for coluna in df.columns]

    # Padronizar possíveis variações do nome da coluna de clima
    if "condicao_meteorologica" in df.columns and "condicao_metereologica" not in df.columns:
        df = df.rename(columns={"condicao_meteorologica": "condicao_metereologica"})

    if "condicao_meteorologica" in df.columns:
        df = df.rename(columns={"condicao_meteorologica": "condicao_metereologica"})

    # Colunas essenciais para o projeto
    colunas_essenciais = [
        "data_inversa",
        "horario",
        "uf",
        "tipo_acidente",
        "classificacao_acidente",
        "condicao_metereologica"
    ]

    colunas_faltando = [coluna for coluna in colunas_essenciais if coluna not in df.columns]

    if colunas_faltando:
        st.error("Algumas colunas essenciais não foram encontradas no CSV.")
        st.write("Colunas faltando:", colunas_faltando)
        st.write("Colunas encontradas no arquivo:", df.columns.tolist())
        st.stop()

    # Criar colunas opcionais caso não existam
    colunas_categoricas_opcionais = [
        "municipio",
        "causa_acidente",
        "tipo_pista",
        "tracado_via"
    ]

    for coluna in colunas_categoricas_opcionais:
        if coluna not in df.columns:
            df[coluna] = "Não informado"

    colunas_numericas_opcionais = [
        "mortos",
        "feridos_leves",
        "feridos_graves",
        "ilesos",
        "veiculos"
    ]

    for coluna in colunas_numericas_opcionais:
        if coluna not in df.columns:
            df[coluna] = 0

    # Converter data
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")

    # Converter horário
    df["horario"] = pd.to_datetime(df["horario"], format="%H:%M:%S", errors="coerce")

    # Criar ano, mês e hora
    df["ano"] = df["data_inversa"].dt.year
    df["mes"] = df["data_inversa"].dt.month
    df["hora"] = df["horario"].dt.hour

    # Tratar valores nulos em colunas categóricas
    colunas_categoricas = [
        "uf",
        "municipio",
        "causa_acidente",
        "tipo_acidente",
        "classificacao_acidente",
        "condicao_metereologica",
        "tipo_pista",
        "tracado_via"
    ]

    for coluna in colunas_categoricas:
        df[coluna] = df[coluna].fillna("Não informado")
        df[coluna] = df[coluna].astype(str).str.strip()

    # Corrigir textos quebrados por encoding
    df = corrigir_textos_dataframe(df)

    # Tratar colunas numéricas
    colunas_numericas = [
        "mortos",
        "feridos_leves",
        "feridos_graves",
        "ilesos",
        "veiculos"
    ]

    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        df[coluna] = df[coluna].fillna(0)

    return df


df = limpar_dados(df)


# ============================================================
# CRIAÇÃO DE FEATURES
# ============================================================

def criar_features(df):
    df = df.copy()

    # Criar período do dia
    df["periodo_dia"] = pd.cut(
        df["hora"],
        bins=[-1, 5, 11, 17, 23],
        labels=["Madrugada", "Manhã", "Tarde", "Noite"]
    )

    # Normalização textual para comparação interna
    df["condicao_clima_normalizada"] = df["condicao_metereologica"].apply(normalizar_texto_comparacao)

    climas_adversos = {
        "chuva",
        "garoa/chuvisco",
        "nevoeiro/neblina",
        "vento",
        "granizo"
    }

    df["clima_adverso"] = np.where(
        df["condicao_clima_normalizada"].isin(climas_adversos),
        "Clima adverso",
        "Clima normal"
    )

    # Indicadores de gravidade
    df["houve_morte"] = df["mortos"] > 0

    df["total_feridos"] = df["feridos_leves"] + df["feridos_graves"]

    df["houve_feridos"] = df["total_feridos"] > 0

    # Índice de gravidade
    df["indice_gravidade"] = (
        df["mortos"] * 3 +
        df["feridos_graves"] * 2 +
        df["feridos_leves"] * 1
    )

    # Variável alvo para modelo preditivo
    df["acidente_fatal"] = np.where(df["mortos"] > 0, 1, 0)

    return df


df = criar_features(df)


# ============================================================
# PRÉVIA DA BASE TRATADA
# ============================================================

with st.expander("Visualizar prévia da base de dados tratada"):
    st.dataframe(df.head())
    st.write("Colunas disponíveis:", df.columns.tolist())


# ============================================================
# FILTROS
# ============================================================

st.sidebar.header("Filtros da Análise")

ufs = sorted(df["uf"].dropna().unique())
uf_selecionada = st.sidebar.multiselect(
    "Selecione a UF:",
    options=ufs,
    default=ufs
)

climas = sorted(df["condicao_metereologica"].dropna().unique())
clima_selecionado = st.sidebar.multiselect(
    "Condição meteorológica:",
    options=climas,
    default=climas
)

tipos = sorted(df["tipo_acidente"].dropna().unique())
tipo_selecionado = st.sidebar.multiselect(
    "Tipo de acidente:",
    options=tipos,
    default=tipos
)

df_filtrado = df[
    (df["uf"].isin(uf_selecionada)) &
    (df["condicao_metereologica"].isin(clima_selecionado)) &
    (df["tipo_acidente"].isin(tipo_selecionado))
]


if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()


# ============================================================
# INDICADORES GERAIS
# ============================================================

st.subheader("Indicadores Gerais")

total_acidentes = len(df_filtrado)
total_mortos = int(df_filtrado["mortos"].sum())
total_feridos = int(df_filtrado["total_feridos"].sum())
gravidade_media = df_filtrado["indice_gravidade"].mean()

if pd.isna(gravidade_media):
    gravidade_media = 0

percentual_clima_adverso = (
    (df_filtrado["clima_adverso"] == "Clima adverso").mean() * 100
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total de Acidentes", f"{total_acidentes:,}".replace(",", "."))
col2.metric("Total de Mortos", total_mortos)
col3.metric("Total de Feridos", total_feridos)
col4.metric("Clima Adverso", f"{percentual_clima_adverso:.1f}%")
col5.metric("Gravidade Média", f"{gravidade_media:.2f}")


# ============================================================
# GRÁFICO 1 - ACIDENTES POR CLIMA
# ============================================================

st.subheader("Acidentes por Condição Meteorológica")

acidentes_por_clima = (
    df_filtrado["condicao_metereologica"]
    .value_counts()
    .head(10)
)

fig, ax = plt.subplots(figsize=(10, 5))
acidentes_por_clima.plot(kind="bar", ax=ax)

ax.set_title("Top 10 Condições Meteorológicas com Mais Acidentes")
ax.set_xlabel("Condição Meteorológica")
ax.set_ylabel("Quantidade de Acidentes")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# ============================================================
# GRÁFICO 2 - GRAVIDADE POR CLIMA
# ============================================================

st.subheader("Gravidade Média por Condição Meteorológica")

gravidade_por_clima = (
    df_filtrado
    .groupby("condicao_metereologica")["indice_gravidade"]
    .mean()
    .sort_values(ascending=False)
    .head(10)
)

fig, ax = plt.subplots(figsize=(10, 5))
gravidade_por_clima.plot(kind="bar", ax=ax)

ax.set_title("Gravidade Média dos Acidentes por Condição Meteorológica")
ax.set_xlabel("Condição Meteorológica")
ax.set_ylabel("Índice Médio de Gravidade")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)


# ============================================================
# GRÁFICO 3 - TIPOS DE ACIDENTE EM DIAS DE CHUVA
# ============================================================

st.subheader("Tipos de Acidente em Dias de Chuva")

df_chuva = df_filtrado[
    df_filtrado["condicao_clima_normalizada"].isin(["chuva", "garoa/chuvisco"])
]

tipos_chuva = (
    df_chuva["tipo_acidente"]
    .value_counts()
    .head(10)
)

if tipos_chuva.empty:
    st.info("Não há acidentes com chuva ou garoa nos filtros selecionados.")
else:
    fig, ax = plt.subplots(figsize=(10, 5))
    tipos_chuva.plot(kind="bar", ax=ax)

    ax.set_title("Tipos de Acidente Mais Frequentes em Dias de Chuva")
    ax.set_xlabel("Tipo de Acidente")
    ax.set_ylabel("Quantidade")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


# ============================================================
# GRÁFICO 4 - ACIDENTES POR HORÁRIO
# ============================================================

st.subheader("Acidentes por Horário e Tipo de Clima")

acidentes_hora = (
    df_filtrado
    .dropna(subset=["hora"])
    .groupby(["hora", "clima_adverso"])
    .size()
    .unstack(fill_value=0)
)

if acidentes_hora.empty:
    st.info("Não há dados suficientes para gerar o gráfico por horário.")
else:
    fig, ax = plt.subplots(figsize=(10, 5))
    acidentes_hora.plot(kind="line", marker="o", ax=ax)

    ax.set_title("Distribuição de Acidentes por Hora do Dia")
    ax.set_xlabel("Hora")
    ax.set_ylabel("Quantidade de Acidentes")
    ax.legend(title="Tipo de Clima")
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


# ============================================================
# GRÁFICO 5 - UF COM MAIS ACIDENTES EM CLIMA ADVERSO
# ============================================================

st.subheader("Estados com Mais Acidentes em Clima Adverso")

df_adverso = df_filtrado[df_filtrado["clima_adverso"] == "Clima adverso"]

ranking_uf = (
    df_adverso["uf"]
    .value_counts()
    .head(10)
)

if ranking_uf.empty:
    st.info("Não há registros de clima adverso nos filtros selecionados.")
else:
    fig, ax = plt.subplots(figsize=(10, 5))
    ranking_uf.plot(kind="bar", ax=ax)

    ax.set_title("Top 10 UFs com Mais Acidentes em Clima Adverso")
    ax.set_xlabel("UF")
    ax.set_ylabel("Quantidade de Acidentes")
    ax.tick_params(axis="x", rotation=0)
    fig.tight_layout()

    st.pyplot(fig)
    plt.close(fig)


# ============================================================
# TABELA RESUMO
# ============================================================

st.subheader("Resumo por Condição Meteorológica")

resumo_clima = (
    df_filtrado
    .groupby("condicao_metereologica")
    .agg(
        quantidade_acidentes=("condicao_metereologica", "count"),
        total_mortos=("mortos", "sum"),
        total_feridos=("total_feridos", "sum"),
        gravidade_media=("indice_gravidade", "mean"),
        media_veiculos=("veiculos", "mean")
    )
    .sort_values(by="quantidade_acidentes", ascending=False)
)

st.dataframe(resumo_clima)


# ============================================================
# MODELO PREDITIVO OPCIONAL
# ============================================================

st.subheader("Modelo Preditivo Opcional")

st.markdown("""
O modelo abaixo utiliza Random Forest para estimar se um acidente pode ter vítima fatal
com base em características como clima, tipo de acidente, tipo de pista, traçado da via,
UF, horário e quantidade de veículos.
""")

usar_modelo = st.checkbox("Executar modelo preditivo com Scikit-learn")

if usar_modelo:
    colunas_modelo = [
        "condicao_metereologica",
        "tipo_acidente",
        "tipo_pista",
        "tracado_via",
        "uf",
        "hora",
        "veiculos"
    ]

    df_modelo = df_filtrado[colunas_modelo + ["acidente_fatal"]].copy()
    df_modelo = df_modelo.dropna()

    if len(df_modelo) < 20:
        st.warning("Não há dados suficientes para treinar o modelo com segurança nos filtros atuais.")
    elif df_modelo["acidente_fatal"].nunique() < 2:
        st.warning("Não há classes suficientes para treinar o modelo com os filtros atuais.")
    else:
        X = df_modelo[colunas_modelo]
        y = df_modelo["acidente_fatal"]

        X = pd.get_dummies(X, drop_first=True)

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=y
        )

        modelo = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight="balanced"
        )

        modelo.fit(X_train, y_train)

        y_pred = modelo.predict(X_test)

        acuracia = accuracy_score(y_test, y_pred)
        matriz = confusion_matrix(y_test, y_pred)

        st.metric("Acurácia do Modelo", f"{acuracia:.2%}")

        st.write("Matriz de Confusão:")
        st.dataframe(pd.DataFrame(
            matriz,
            columns=["Previsto: Não Fatal", "Previsto: Fatal"],
            index=["Real: Não Fatal", "Real: Fatal"]
        ))

        importancias = pd.Series(
            modelo.feature_importances_,
            index=X.columns
        ).sort_values(ascending=False).head(10)

        st.write("Principais variáveis usadas pelo modelo:")

        fig, ax = plt.subplots(figsize=(10, 5))
        importancias.plot(kind="bar", ax=ax)

        ax.set_title("Top 10 Variáveis Mais Relevantes para o Modelo")
        ax.set_xlabel("Variável")
        ax.set_ylabel("Importância")
        ax.tick_params(axis="x", rotation=45)
        fig.tight_layout()

        st.pyplot(fig)
        plt.close(fig)

        st.info("""
        Observação: este modelo identifica padrões estatísticos nos dados, mas não prova causalidade.
        Ou seja, ele não afirma que o clima causa diretamente acidentes fatais, apenas mostra associações
        presentes na base analisada.
        """)


# ============================================================
# CONCLUSÃO
# ============================================================

st.subheader("Conclusão da Análise")

if not acidentes_por_clima.empty:
    clima_mais_frequente = acidentes_por_clima.idxmax()
else:
    clima_mais_frequente = "Não identificado"

if not tipos_chuva.empty:
    tipo_chuva_mais_comum = tipos_chuva.idxmax()
else:
    tipo_chuva_mais_comum = "Não identificado nos filtros selecionados"

st.markdown(f"""
A análise mostra que a condição meteorológica com maior número de acidentes na base filtrada foi 
**{clima_mais_frequente}**.

Em dias de chuva ou garoa, o tipo de acidente mais frequente foi 
**{tipo_chuva_mais_comum}**.

O percentual de acidentes em clima adverso foi de **{percentual_clima_adverso:.1f}%**,
indicando que fatores meteorológicos devem ser considerados em campanhas de prevenção,
ações de fiscalização e estratégias de segurança viária.

Além disso, o índice de gravidade criado no projeto permite comparar não apenas a quantidade
de acidentes, mas também o impacto gerado por mortos e feridos. Isso torna a análise mais
completa e útil para tomada de decisão.
""")
