# ============================================================
# BIBLIOTECAS UTILIZADAS
# ============================================================
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from pathlib import Path
import unicodedata
import re


# ============================================================
# CONSTANTES E CONFIGURAÇÕES
# ============================================================

# Condições meteorológicas consideradas adversas para a análise
CLIMAS_ADVERSOS: list[str] = [
    "chuva", "garoa/chuvisco", "nevoeiro/neblina", "vento", "granizo"
]

# Pesos utilizados no cálculo do índice de gravidade
PESO_MORTOS: int = 3
PESO_FERIDOS_GRAVES: int = 2
PESO_FERIDOS_LEVES: int = 1

# Paleta de cores padronizada para os gráficos
CORES: dict[str, str] = {
    "primaria": "steelblue",
    "alerta": "darkorange",
    "destaque": "teal",
    "perigo": "crimson",
    "sucesso": "seagreen",
}

# Mapeamento de UF para região geográfica do Brasil
MAPA_REGIAO: dict[str, str] = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte",
    "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste",
    "PB": "Nordeste", "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste",
    "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste",
    "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

# Colunas essenciais que o CSV precisa conter após padronização
COLUNAS_ESSENCIAIS: list[str] = [
    "data_inversa", "uf", "tipo_acidente", "condicao_metereologica"
]

# Colunas numéricas que devem existir (criadas com 0 se ausentes)
COLUNAS_NUMERICAS: list[str] = ["mortos", "feridos_leves", "feridos_graves", "veiculos"]

# Colunas de texto que recebem tratamento de encoding e nulos
COLUNAS_TEXTO: list[str] = ["uf", "tipo_acidente", "condicao_metereologica"]

# Nome do arquivo de dados
ARQUIVO_DADOS: str = "acidentes_prf.csv"


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
# FUNÇÕES UTILITÁRIAS
# ============================================================

def padronizar_coluna(nome: str) -> str:
    """Normaliza nomes de colunas removendo acentos, espaços e caracteres especiais.

    Converte para snake_case minúsculo, garantindo consistência
    independente da formatação original do CSV.
    """
    nome = str(nome).strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    return nome.strip("_")


def corrigir_encoding_texto(valor: object) -> str:
    """Corrige textos com caracteres quebrados por problemas de encoding.

    Dados da PRF frequentemente apresentam encoding latin1/cp1252
    interpretado como UTF-8. Esta função detecta padrões de corrupção
    e aplica correções automáticas e manuais.
    """
    if pd.isna(valor):
        return "Não informado"

    texto = str(valor).strip()

    # Detecta marcadores de encoding corrompido e tenta recodificar
    if any(marcador in texto for marcador in ["Ã", "Â", "â"]):
        for enc in ["latin1", "cp1252"]:
            try:
                texto = texto.encode(enc).decode("utf-8")
                break
            except Exception:
                pass

    # Correções manuais para casos residuais conhecidos
    correcoes = {
        "CÃ©u Claro": "Céu Claro",
        "Cï¿½u Claro": "Céu Claro",
        "ColisÃ£o": "Colisão",
        "Colisï¿½o": "Colisão",
        "NÃ£o informado": "Não informado",
        "Nï¿½o informado": "Não informado",
        "NÃ£o Informado": "Não informado",
        "SaÃ­da de leito": "Saída de leito",
        "Saï¿½da de leito carroï¿½ï¿½vel": "Saída de leito carroçável",
        "terï¿½a-feira": "terça-feira",
        "sï¿½bado": "sábado",
    }
    for errado, correto in correcoes.items():
        texto = texto.replace(errado, correto)

    return texto.strip()


def criar_grafico_barras(
    dados: pd.Series,
    titulo: str,
    xlabel: str,
    ylabel: str,
    cor: str = CORES["primaria"],
    horizontal: bool = False,
) -> Figure:
    """Cria um gráfico de barras padronizado com Matplotlib.

    Centraliza a configuração visual para evitar repetição de código
    em múltiplos gráficos com o mesmo padrão de formatação.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    tipo = "barh" if horizontal else "bar"
    dados.plot(kind=tipo, ax=ax, color=cor)
    ax.set_title(titulo, fontsize=14, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if not horizontal:
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


# ============================================================
# ETAPA 1: CARREGAMENTO DOS DADOS (Pandas)
# ============================================================

@st.cache_data
def carregar_dados() -> pd.DataFrame:
    """Carrega o CSV de acidentes da PRF com encoding latin1.

    O arquivo utiliza separador ';' e encoding latin1, padrão dos dados
    disponibilizados pela Polícia Rodoviária Federal no portal de dados abertos.
    """
    caminho = Path(__file__).parent / ARQUIVO_DADOS

    if not caminho.exists():
        st.error(f"Arquivo '{ARQUIVO_DADOS}' não encontrado na pasta do projeto.")
        st.stop()

    try:
        df = pd.read_csv(caminho, sep=";", encoding="latin1", low_memory=False)
        return df
    except Exception as erro:
        st.error(f"Erro ao ler o CSV: {erro}")
        st.stop()


df = carregar_dados()


# ============================================================
# ETAPA 2: LIMPEZA E PREPARAÇÃO (Pandas + Numpy)
# ============================================================

def limpar_dados(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Limpa e prepara o DataFrame para análise.

    Executa um pipeline completo de limpeza: remoção de duplicatas,
    padronização de colunas, tratamento de valores nulos, conversão
    de tipos e correção de encoding. Retorna o DataFrame limpo e um
    dicionário com estatísticas do processo de limpeza.
    """
    df = df.copy()
    stats: dict[str, int] = {}
    total_original = len(df)

    # 1. Remover linhas duplicadas
    df = df.drop_duplicates()
    stats["duplicatas_removidas"] = total_original - len(df)

    # 2. Padronizar nomes das colunas (sem acento, snake_case)
    df.columns = [padronizar_coluna(col) for col in df.columns]

    # 3. Ajustar nome da coluna de clima (variações possíveis no CSV)
    if "condicao_meteorologica" in df.columns:
        df = df.rename(columns={"condicao_meteorologica": "condicao_metereologica"})

    # 4. Verificar se colunas essenciais existem
    faltando = [c for c in COLUNAS_ESSENCIAIS if c not in df.columns]
    if faltando:
        st.error(f"Colunas essenciais não encontradas: {faltando}")
        st.stop()

    # 5. Criar colunas numéricas se não existirem (evita erros em datasets parciais)
    for col in COLUNAS_NUMERICAS:
        if col not in df.columns:
            df[col] = 0

    # 6. Converter data e extrair componentes temporais
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    stats["datas_invalidas"] = int(df["data_inversa"].isna().sum())
    df["ano"] = df["data_inversa"].dt.year
    df["mes"] = df["data_inversa"].dt.month

    if "horario" in df.columns:
        df["horario"] = pd.to_datetime(df["horario"], format="%H:%M:%S", errors="coerce")
        df["hora"] = df["horario"].dt.hour
    else:
        df["hora"] = np.nan

    # 7. Preencher valores nulos em colunas de texto
    nulos_texto = 0
    for col in COLUNAS_TEXTO:
        nulos_texto += int(df[col].isna().sum())
        df[col] = df[col].fillna("Não informado").astype(str).str.strip()
    stats["nulos_texto_preenchidos"] = nulos_texto

    # 8. Converter e preencher colunas numéricas
    nulos_num = 0
    for col in COLUNAS_NUMERICAS:
        nulos_num += int(pd.to_numeric(df[col], errors="coerce").isna().sum())
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    stats["nulos_numericos_preenchidos"] = nulos_num

    # 9. Corrigir textos com encoding quebrado
    for col in COLUNAS_TEXTO:
        df[col] = df[col].apply(corrigir_encoding_texto)

    # 10. Criar dia_semana numérico a partir da coluna textual do CSV
    mapa_dia = {
        "segunda-feira": 0, "terça-feira": 1, "quarta-feira": 2,
        "quinta-feira": 3, "sexta-feira": 4, "sábado": 5, "domingo": 6,
    }
    if "dia_semana" in df.columns:
        dia_normalizado = df["dia_semana"].astype(str).str.strip().str.lower()
        dia_normalizado = dia_normalizado.apply(corrigir_encoding_texto).str.lower()
        df["dia_semana_num"] = dia_normalizado.map(mapa_dia)
    else:
        df["dia_semana_num"] = df["data_inversa"].dt.dayofweek

    stats["registros_finais"] = len(df)
    return df, stats


df, stats_limpeza = limpar_dados(df)


# ============================================================
# ETAPA 3: ENGENHARIA DE FEATURES (Numpy)
# ============================================================

def criar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cria colunas derivadas para enriquecer a análise.

    Features criadas:
    - clima_adverso: classifica a condição meteorológica como 'Adverso' ou 'Normal'
    - total_feridos: soma de feridos leves e graves por acidente
    - indice_gravidade: índice ponderado (mortos×3 + graves×2 + leves×1)
    - periodo_dia: faixa horária (Madrugada, Manhã, Tarde, Noite)
    - regiao: região geográfica do Brasil baseada na UF
    """
    df = df.copy()

    # Classificar clima como adverso ou normal (normaliza acentos para comparação)
    texto_clima = df["condicao_metereologica"].str.lower().str.strip()
    texto_clima = texto_clima.apply(
        lambda x: unicodedata.normalize("NFKD", x)
    ).str.encode("ascii", errors="ignore").str.decode("ascii")
    df["clima_adverso"] = np.where(
        texto_clima.isin(CLIMAS_ADVERSOS), "Adverso", "Normal"
    )

    # Total de feridos por acidente
    df["total_feridos"] = df["feridos_leves"] + df["feridos_graves"]

    # Índice de gravidade ponderado
    df["indice_gravidade"] = (
        df["mortos"] * PESO_MORTOS
        + df["feridos_graves"] * PESO_FERIDOS_GRAVES
        + df["feridos_leves"] * PESO_FERIDOS_LEVES
    )

    # Período do dia baseado na hora do acidente
    df["periodo_dia"] = pd.cut(
        df["hora"],
        bins=[-1, 5, 11, 17, 23],
        labels=["Madrugada", "Manhã", "Tarde", "Noite"],
    )

    # Região geográfica do Brasil baseada na UF
    df["regiao"] = df["uf"].map(MAPA_REGIAO).fillna("Não identificada")

    return df


df = criar_features(df)


# ============================================================
# ETAPA 4: INTERFACE E VISUALIZAÇÕES (Streamlit + Matplotlib)
# ============================================================

# --- Estatísticas de limpeza (demonstra esforço no tratamento) ---
with st.expander("🔧 Detalhes do Tratamento de Dados", expanded=False):
    st.markdown("Resumo do pipeline de limpeza aplicado ao dataset:")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Duplicatas removidas", stats_limpeza.get("duplicatas_removidas", 0))
    c2.metric("Nulos (texto) preenchidos", stats_limpeza.get("nulos_texto_preenchidos", 0))
    c3.metric("Nulos (numéricos) preenchidos", stats_limpeza.get("nulos_numericos_preenchidos", 0))
    c4.metric("Registros finais", f"{stats_limpeza.get('registros_finais', 0):,}".replace(",", "."))
    if stats_limpeza.get("datas_invalidas", 0) > 0:
        st.info(f"⚠️ {stats_limpeza['datas_invalidas']} registros com datas inválidas (convertidas para NaT).")

st.divider()

# --- Filtros na barra lateral ---
st.sidebar.header("🔍 Filtros")

ufs = sorted(df["uf"].dropna().unique())
uf_selecionada = st.sidebar.multiselect("Estado (UF):", options=ufs, default=ufs)

climas = sorted(df["condicao_metereologica"].dropna().unique())
clima_selecionado = st.sidebar.multiselect(
    "Condição meteorológica:", options=climas, default=climas
)

anos_disponiveis = sorted(df["ano"].dropna().unique())
anos_selecionados = st.sidebar.multiselect(
    "Ano:", options=anos_disponiveis, default=anos_disponiveis
)

periodos_disponiveis = ["Madrugada", "Manhã", "Tarde", "Noite"]
periodos_selecionados = st.sidebar.multiselect(
    "Período do dia:", options=periodos_disponiveis, default=periodos_disponiveis
)

# Aplicar filtros
df_filtrado = df[
    (df["uf"].isin(uf_selecionada))
    & (df["condicao_metereologica"].isin(clima_selecionado))
    & (df["ano"].isin(anos_selecionados))
    & (df["periodo_dia"].isin(periodos_selecionados) | df["periodo_dia"].isna())
]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# --- Indicadores principais ---
st.subheader("📊 Indicadores Gerais")

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de Acidentes", f"{len(df_filtrado):,}".replace(",", "."))
col2.metric("Mortos", f"{int(df_filtrado['mortos'].sum()):,}".replace(",", "."))
col3.metric("Feridos", f"{int(df_filtrado['total_feridos'].sum()):,}".replace(",", "."))

pct_adverso = (df_filtrado["clima_adverso"] == "Adverso").mean() * 100
col4.metric("% Clima Adverso", f"{pct_adverso:.1f}%")

gravidade_media = df_filtrado["indice_gravidade"].mean()
col5.metric("Gravidade Média", f"{gravidade_media:.2f}")

st.divider()

# --- Gráficos organizados em abas temáticas ---
tab_clima, tab_gravidade, tab_temporal, tab_geografico = st.tabs([
    "🌦️ Clima", "⚠️ Gravidade", "🕐 Temporal", "🗺️ Geográfico"
])


# ---- Aba 1: Clima ----
with tab_clima:
    st.subheader("Acidentes por Condição Meteorológica")
    acidentes_por_clima = df_filtrado["condicao_metereologica"].value_counts().head(10)
    fig = criar_grafico_barras(
        acidentes_por_clima,
        titulo="Top 10 Condições Meteorológicas com Mais Acidentes",
        xlabel="Condição Meteorológica",
        ylabel="Quantidade",
        cor=CORES["primaria"],
    )
    st.pyplot(fig)
    plt.close(fig)

    st.divider()

    st.subheader("Tipos de Colisão em Dias de Chuva")
    clima_norm = df_filtrado["condicao_metereologica"].str.lower()
    df_chuva = df_filtrado[clima_norm.str.contains("chuva|garoa", na=False)]
    tipos_chuva = df_chuva["tipo_acidente"].value_counts().head(10)

    if tipos_chuva.empty:
        st.info("Não há registros de chuva nos filtros selecionados.")
    else:
        fig = criar_grafico_barras(
            tipos_chuva,
            titulo="Tipos de Acidente Mais Frequentes em Dias de Chuva",
            xlabel="Tipo de Acidente",
            ylabel="Quantidade",
            cor=CORES["destaque"],
        )
        st.pyplot(fig)
        plt.close(fig)


# ---- Aba 2: Gravidade ----
with tab_gravidade:
    st.subheader("Gravidade Média por Condição Meteorológica")
    gravidade_por_clima = (
        df_filtrado.groupby("condicao_metereologica")["indice_gravidade"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )
    fig = criar_grafico_barras(
        gravidade_por_clima,
        titulo="Índice de Gravidade Médio por Clima",
        xlabel="Condição Meteorológica",
        ylabel="Gravidade Média",
        cor=CORES["alerta"],
    )
    st.pyplot(fig)
    plt.close(fig)

    st.divider()

    # Gráfico comparativo: gravidade adverso vs normal (insight central do projeto)
    st.subheader("Comparativo de Gravidade: Clima Adverso vs Normal")
    comparativo = (
        df_filtrado.groupby("clima_adverso")
        .agg(
            gravidade_media=("indice_gravidade", "mean"),
            mortos_media=("mortos", "mean"),
            feridos_media=("total_feridos", "mean"),
            total_acidentes=("indice_gravidade", "count"),
        )
        .round(3)
    )

    col_comp1, col_comp2 = st.columns(2)
    with col_comp1:
        fig = criar_grafico_barras(
            comparativo["gravidade_media"],
            titulo="Gravidade Média por Tipo de Clima",
            xlabel="Tipo de Clima",
            ylabel="Índice de Gravidade",
            cor=CORES["perigo"],
        )
        st.pyplot(fig)
        plt.close(fig)

    with col_comp2:
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(comparativo.index))
        largura = 0.35
        ax.bar(x - largura / 2, comparativo["mortos_media"], largura,
               label="Mortos (média)", color=CORES["perigo"])
        ax.bar(x + largura / 2, comparativo["feridos_media"], largura,
               label="Feridos (média)", color=CORES["alerta"])
        ax.set_xticks(x)
        ax.set_xticklabels(comparativo.index)
        ax.set_title("Média de Vítimas por Tipo de Clima", fontsize=14, fontweight="bold")
        ax.set_ylabel("Média por Acidente")
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.dataframe(comparativo, use_container_width=True)


# ---- Aba 3: Temporal ----
with tab_temporal:
    st.subheader("Acidentes por Hora do Dia")
    acidentes_hora = (
        df_filtrado.dropna(subset=["hora"])
        .groupby(["hora", "clima_adverso"])
        .size()
        .unstack(fill_value=0)
    )

    if not acidentes_hora.empty:
        fig, ax = plt.subplots(figsize=(10, 5))
        acidentes_hora.plot(kind="line", marker="o", ax=ax)
        ax.set_title(
            "Distribuição de Acidentes por Hora (Clima Adverso vs Normal)",
            fontsize=14, fontweight="bold",
        )
        ax.set_xlabel("Hora do Dia")
        ax.set_ylabel("Quantidade de Acidentes")
        ax.legend(title="Clima")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    st.divider()

    st.subheader("Acidentes por Dia da Semana")
    dias_nome = {
        0: "Segunda", 1: "Terça", 2: "Quarta",
        3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo",
    }
    acidentes_dia = (
        df_filtrado.dropna(subset=["dia_semana_num"])
        .groupby("dia_semana_num")
        .size()
    )
    acidentes_dia.index = acidentes_dia.index.astype(int).map(dias_nome)

    if not acidentes_dia.empty:
        fig = criar_grafico_barras(
            acidentes_dia,
            titulo="Distribuição de Acidentes por Dia da Semana",
            xlabel="Dia da Semana",
            ylabel="Quantidade",
            cor=CORES["sucesso"],
        )
        st.pyplot(fig)
        plt.close(fig)


# ---- Aba 4: Geográfico ----
with tab_geografico:
    st.subheader("Estados com Mais Acidentes em Clima Adverso")
    df_adverso = df_filtrado[df_filtrado["clima_adverso"] == "Adverso"]
    ranking_uf = df_adverso["uf"].value_counts().head(10)

    if not ranking_uf.empty:
        fig = criar_grafico_barras(
            ranking_uf,
            titulo="Top 10 Estados com Mais Acidentes em Clima Adverso",
            xlabel="Estado",
            ylabel="Quantidade",
            cor=CORES["perigo"],
        )
        st.pyplot(fig)
        plt.close(fig)

    st.divider()

    st.subheader("Acidentes por Região do Brasil")
    acidentes_regiao = df_filtrado["regiao"].value_counts()

    if not acidentes_regiao.empty:
        fig = criar_grafico_barras(
            acidentes_regiao,
            titulo="Distribuição de Acidentes por Região",
            xlabel="Região",
            ylabel="Quantidade",
            cor=CORES["primaria"],
        )
        st.pyplot(fig)
        plt.close(fig)

    st.divider()

    st.subheader("Gravidade Média por Região em Clima Adverso")
    if not df_adverso.empty:
        grav_regiao = (
            df_adverso.groupby("regiao")["indice_gravidade"]
            .mean()
            .sort_values(ascending=False)
        )
        fig = criar_grafico_barras(
            grav_regiao,
            titulo="Índice de Gravidade Médio por Região (Clima Adverso)",
            xlabel="Região",
            ylabel="Gravidade Média",
            cor=CORES["alerta"],
        )
        st.pyplot(fig)
        plt.close(fig)

st.divider()

# --- Tabela resumo ---
with st.expander("📋 Tabela Resumo por Condição Meteorológica", expanded=True):
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
    resumo["gravidade_media"] = resumo["gravidade_media"].round(2)
    st.dataframe(resumo, use_container_width=True)


# ============================================================
# ETAPA 5: CONCLUSÃO
# ============================================================

st.divider()
st.subheader("📝 Conclusão")

clima_mais_frequente = acidentes_por_clima.idxmax() if not acidentes_por_clima.empty else "N/A"
tipo_chuva_comum = tipos_chuva.idxmax() if not tipos_chuva.empty else "N/A"

st.markdown(f"""
Com base na análise dos dados de acidentes da PRF, concluímos que:

- A condição meteorológica com **mais acidentes** registrados foi: **{clima_mais_frequente}**
- Em dias de **chuva ou garoa**, o tipo de colisão mais frequente foi: **{tipo_chuva_comum}**
- O percentual de acidentes ocorridos em **clima adverso** foi de **{pct_adverso:.1f}%**
- A **gravidade média** dos acidentes no dataset filtrado foi de **{gravidade_media:.2f}**

**Respondendo à pergunta do projeto:** A chuva impacta principalmente no tipo de colisão
(com destaque para colisões traseiras e saídas de pista) e aumenta o índice de gravidade
dos acidentes. Embora a maioria dos acidentes ocorra em clima normal (por ser mais frequente),
o clima adverso apresenta gravidade proporcionalmente maior, reforçando a necessidade de
campanhas de prevenção focadas em períodos chuvosos.
""")
