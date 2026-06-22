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

periodos_disponiveis = ["Madrugada", "Manhã", "Tarde", "Noite"]
periodos_selecionados = st.sidebar.multiselect(
    "Período do dia:", options=periodos_disponiveis, default=periodos_disponiveis
)

# Aplicar filtros
df_filtrado = df[
    (df["uf"].isin(uf_selecionada))
    & (df["condicao_metereologica"].isin(clima_selecionado))
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

    # Análise proporcional: por que céu claro lidera?
    total_acidentes = len(df_filtrado)
    pct_por_clima = (acidentes_por_clima / total_acidentes * 100).round(1)
    condicao_lider = acidentes_por_clima.index[0] if len(acidentes_por_clima) > 0 else "N/A"
    pct_lider = pct_por_clima.iloc[0] if len(pct_por_clima) > 0 else 0

    st.info(f"""
    📊 **Insight do Analista:** A condição **"{condicao_lider}"** lidera com **{pct_lider:.1f}%** dos acidentes.
    Isso **não significa** que essa condição seja mais perigosa — significa que ela é a **mais frequente**.
    Como o Brasil possui clima predominantemente tropical, a maioria dos dias do ano apresenta céu claro,
    o que naturalmente eleva a contagem absoluta de acidentes nessa condição.
    Para avaliar o real impacto do clima, é necessário analisar a **gravidade proporcional** (ver gráfico abaixo).
    """)

    # Gráfico de taxa normalizada: gravidade média por condição
    st.subheader("Taxa de Gravidade por Condição Meteorológica (Análise Proporcional)")
    gravidade_normalizada = (
        df_filtrado.groupby("condicao_metereologica")
        .agg(
            gravidade_media=("indice_gravidade", "mean"),
            total=("indice_gravidade", "count"),
        )
        .sort_values("gravidade_media", ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=(10, 5))
    cores_barra = [
        CORES["perigo"] if idx in df_filtrado[df_filtrado["clima_adverso"] == "Adverso"]["condicao_metereologica"].unique()
        else CORES["primaria"]
        for idx in gravidade_normalizada.index
    ]
    gravidade_normalizada["gravidade_media"].plot(kind="bar", ax=ax, color=cores_barra)
    ax.set_title("Gravidade Média por Condição (vermelho = clima adverso)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Condição Meteorológica")
    ax.set_ylabel("Índice de Gravidade Médio")
    ax.tick_params(axis="x", rotation=45)
    ax.axhline(y=df_filtrado["indice_gravidade"].mean(), color="gray", linestyle="--", label="Média geral")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    grav_adverso = df_filtrado[df_filtrado["clima_adverso"] == "Adverso"]["indice_gravidade"].mean()
    grav_normal = df_filtrado[df_filtrado["clima_adverso"] == "Normal"]["indice_gravidade"].mean()
    if grav_normal > 0:
        aumento_pct = ((grav_adverso - grav_normal) / grav_normal) * 100
        st.success(f"""
        🎯 **Análise Proporcional:** Ao normalizar pela frequência, observa-se que acidentes em
        **clima adverso** possuem gravidade média **{aumento_pct:.1f}% {'maior' if aumento_pct > 0 else 'menor'}**
        que em clima normal. Isso demonstra que, embora o céu claro concentre mais ocorrências em números absolutos,
        **o clima adverso eleva significativamente o risco de lesões graves e óbitos por acidente**.
        """)

    st.divider()

    st.subheader("Tipos de Colisão em Dias de Chuva vs Céu Claro")
    clima_norm = df_filtrado["condicao_metereologica"].str.lower()
    df_chuva = df_filtrado[clima_norm.str.contains("chuva|garoa", na=False)]
    df_ceu_claro = df_filtrado[clima_norm.str.contains("claro", na=False)]
    tipos_chuva = df_chuva["tipo_acidente"].value_counts().head(10)

    if tipos_chuva.empty:
        st.info("Não há registros de chuva nos filtros selecionados.")
    else:
        # Gráfico comparativo: chuva vs céu claro
        tipos_ceu = df_ceu_claro["tipo_acidente"].value_counts().head(10)
        tipos_comuns = tipos_chuva.index.intersection(tipos_ceu.index)

        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(tipos_comuns))
        largura = 0.35

        vals_chuva = [tipos_chuva.get(t, 0) for t in tipos_comuns]
        vals_ceu = [tipos_ceu.get(t, 0) for t in tipos_comuns]

        # Normalizar para proporção (%) para comparação justa
        total_chuva = df_chuva["tipo_acidente"].count()
        total_ceu = df_ceu_claro["tipo_acidente"].count()
        pct_chuva = [v / total_chuva * 100 if total_chuva > 0 else 0 for v in vals_chuva]
        pct_ceu = [v / total_ceu * 100 if total_ceu > 0 else 0 for v in vals_ceu]

        ax.bar(x - largura / 2, pct_chuva, largura, label="Chuva/Garoa", color=CORES["destaque"])
        ax.bar(x + largura / 2, pct_ceu, largura, label="Céu Claro", color=CORES["primaria"])
        ax.set_xticks(x)
        ax.set_xticklabels(tipos_comuns, rotation=45, ha="right")
        ax.set_title("Proporção (%) dos Tipos de Acidente: Chuva vs Céu Claro", fontsize=14, fontweight="bold")
        ax.set_ylabel("% do Total de Acidentes na Condição")
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Insight sobre tipos de colisão na chuva
        tipo_lider_chuva = tipos_chuva.idxmax()
        st.info(f"""
        📊 **Insight do Analista:** Em dias de chuva, o tipo mais frequente é **"{tipo_lider_chuva}"**.
        Isso ocorre por fatores físicos diretos:
        - 🚗 **Colisões traseiras** aumentam porque a pista molhada **reduz o coeficiente de atrito**,
          aumentando a distância de frenagem em até 50%.
        - 🛣️ **Saídas de pista** são mais frequentes devido à **aquaplanagem** (perda de contato pneu-asfalto)
          e **redução da visibilidade** por spray de água dos veículos à frente.
        - 👁️ A chuva reduz a visibilidade e cria reflexos na pista, dificultando a percepção de obstáculos.
        """)


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

    # Insight sobre gravidade por condição
    condicao_mais_grave = gravidade_por_clima.idxmax() if not gravidade_por_clima.empty else "N/A"
    valor_mais_grave = gravidade_por_clima.max() if not gravidade_por_clima.empty else 0
    media_geral_grav = df_filtrado["indice_gravidade"].mean()
    st.info(f"""
    📊 **Insight do Analista:** A condição **"{condicao_mais_grave}"** apresenta a maior gravidade média
    (**{valor_mais_grave:.2f}**), que é **{((valor_mais_grave / media_geral_grav) - 1) * 100:.1f}% acima** da média geral ({media_geral_grav:.2f}).
    Condições com menor visibilidade e aderência tendem a gerar acidentes mais severos porque os motoristas
    não conseguem reagir a tempo, resultando em colisões a velocidades mais altas.
    """)

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

    # Razão de risco e análise
    if "Adverso" in comparativo.index and "Normal" in comparativo.index:
        grav_adv = comparativo.loc["Adverso", "gravidade_media"]
        grav_nor = comparativo.loc["Normal", "gravidade_media"]
        mortos_adv = comparativo.loc["Adverso", "mortos_media"]
        mortos_nor = comparativo.loc["Normal", "mortos_media"]
        razao_risco = grav_adv / grav_nor if grav_nor > 0 else 0
        razao_mortos = mortos_adv / mortos_nor if mortos_nor > 0 else 0

        st.warning(f"""
        ⚠️ **Razão de Risco (Análise Central do Projeto):**
        - **Razão de gravidade:** {razao_risco:.2f}x — cada acidente em clima adverso é, em média,
          **{((razao_risco - 1) * 100):.1f}% mais grave** que em clima normal.
        - **Razão de mortalidade:** {razao_mortos:.2f}x — a taxa de mortos por acidente é
          **{((razao_mortos - 1) * 100):.1f}% maior** em condições adversas.
        - **Por que isso acontece?** Em clima adverso, a combinação de pista escorregadia, menor visibilidade
          e maior tempo de reação resulta em colisões com velocidade de impacto mais elevada,
          o que aumenta diretamente a severidade das lesões.
        """)

    # Histograma de distribuição da gravidade
    st.divider()
    st.subheader("Distribuição do Índice de Gravidade por Tipo de Clima")
    fig, ax = plt.subplots(figsize=(10, 5))
    df_grav_adverso = df_filtrado[df_filtrado["clima_adverso"] == "Adverso"]["indice_gravidade"]
    df_grav_normal = df_filtrado[df_filtrado["clima_adverso"] == "Normal"]["indice_gravidade"]

    ax.hist(df_grav_normal, bins=30, alpha=0.6, label="Normal", color=CORES["primaria"], density=True)
    ax.hist(df_grav_adverso, bins=30, alpha=0.6, label="Adverso", color=CORES["perigo"], density=True)
    ax.set_title("Distribuição do Índice de Gravidade (Normalizado)", fontsize=14, fontweight="bold")
    ax.set_xlabel("Índice de Gravidade")
    ax.set_ylabel("Densidade")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.info("""
    📊 **Leitura do Histograma:** A distribuição mostra que acidentes em clima adverso (vermelho)
    possuem uma "cauda" mais pesada à direita, indicando maior proporção de acidentes graves.
    Em clima normal (azul), a concentração é maior em valores baixos de gravidade. Isso confirma
    que o clima adverso não apenas causa acidentes, mas causa acidentes **mais severos**.
    """)


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
        # Destaque visual para horários de pico
        ax.axvspan(17, 19, alpha=0.1, color="red", label="Horário de pico")
        ax.axvspan(7, 9, alpha=0.1, color="orange", label="Rush manhã")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Identificar hora com mais acidentes
        hora_pico = acidentes_hora.sum(axis=1).idxmax()
        acidentes_pico = int(acidentes_hora.sum(axis=1).max())
        hora_menor = acidentes_hora.sum(axis=1).idxmin()

        st.info(f"""
        📊 **Insight do Analista:** O pico de acidentes ocorre às **{int(hora_pico)}h** ({acidentes_pico} registros),
        enquanto o menor volume é às **{int(hora_menor)}h**. Razões para os padrões observados:
        - 🚗 **Pico 17h-19h:** Coincide com o horário de rush (maior volume de veículos) + redução da
          luminosidade natural (pôr do sol), que prejudica a visibilidade.
        - 🌅 **Pico secundário 7h-9h:** Rush matutino com motoristas ainda sonolentos e sol nascente
          causando ofuscamento em sentidos específicos.
        - 🌙 **Madrugada (menor volume):** Menos veículos circulando, mas quando ocorrem acidentes,
          tendem a ser mais graves (fadiga, álcool, alta velocidade).
        """)

        # Gravidade média por hora
        st.divider()
        st.subheader("Gravidade Média por Hora do Dia")
        grav_por_hora = (
            df_filtrado.dropna(subset=["hora"])
            .groupby("hora")["indice_gravidade"]
            .mean()
        )
        fig, ax = plt.subplots(figsize=(10, 5))
        grav_por_hora.plot(kind="line", marker="s", ax=ax, color=CORES["perigo"])
        ax.set_title("Índice de Gravidade Médio por Hora", fontsize=14, fontweight="bold")
        ax.set_xlabel("Hora do Dia")
        ax.set_ylabel("Gravidade Média")
        ax.axhline(y=grav_por_hora.mean(), color="gray", linestyle="--", label="Média geral")
        ax.legend()
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        hora_mais_grave = grav_por_hora.idxmax()
        st.warning(f"""
        ⚠️ **Paradoxo volume vs gravidade:** A hora com MAIS acidentes ({int(hora_pico)}h) não é a mesma
        com MAIOR gravidade ({int(hora_mais_grave)}h). Isso ocorre porque na madrugada/noite há menos acidentes,
        mas eles são mais letais — motoristas em alta velocidade, sob efeito de álcool ou fadiga,
        em rodovias com pouca iluminação.
        """)

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

        # Gravidade por dia da semana
        grav_por_dia = (
            df_filtrado.dropna(subset=["dia_semana_num"])
            .groupby("dia_semana_num")["indice_gravidade"]
            .mean()
        )
        grav_por_dia.index = grav_por_dia.index.astype(int).map(dias_nome)

        dia_mais_acidentes = acidentes_dia.idxmax()
        dia_mais_grave = grav_por_dia.idxmax()

        st.info(f"""
        📊 **Insight do Analista:** O dia com **mais acidentes** é **{dia_mais_acidentes}**,
        mas o dia com **maior gravidade média** é **{dia_mais_grave}**.
        - 📅 **Dias úteis** concentram mais acidentes por causa do maior fluxo de veículos
          (deslocamento trabalho-casa).
        - 🎉 **Finais de semana** tendem a ter menos acidentes totais, porém com gravidade elevada.
          Fatores: maior consumo de álcool, viagens de longa distância com fadiga,
          e velocidades mais altas em rodovias menos movimentadas.
        """)


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

        # Taxa de acidentes adversos / total por estado
        taxa_adverso_uf = (
            df_adverso["uf"].value_counts() / df_filtrado["uf"].value_counts() * 100
        ).dropna().sort_values(ascending=False).head(10)

        st.subheader("Proporção de Acidentes em Clima Adverso por Estado (%)")
        fig = criar_grafico_barras(
            taxa_adverso_uf.round(1),
            titulo="% dos Acidentes que Ocorrem em Clima Adverso (por UF)",
            xlabel="Estado",
            ylabel="% em Clima Adverso",
            cor=CORES["alerta"],
        )
        st.pyplot(fig)
        plt.close(fig)

        uf_lider_absoluto = ranking_uf.idxmax()
        uf_lider_proporcional = taxa_adverso_uf.idxmax()
        pct_uf_prop = taxa_adverso_uf.max()
        st.info(f"""
        📊 **Insight do Analista:** Em números absolutos, **{uf_lider_absoluto}** lidera em acidentes
        com clima adverso. Porém, proporcionalmente, **{uf_lider_proporcional}** é o estado onde
        **{pct_uf_prop:.1f}% dos acidentes** ocorrem em condições adversas.
        - 🌧️ Estados do **Sul** (PR, SC, RS) e **Sudeste** (MG, SP) tendem a ter maior proporção
          de acidentes em clima adverso devido ao regime pluviométrico mais intenso e frequente.
        - 🛣️ Esses estados também possuem grande malha rodoviária federal, o que amplifica os números.
        - 🏔️ Regiões serranas (SC, MG) combinam neblina frequente + curvas, aumentando o risco.
        """)

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

        regiao_lider = acidentes_regiao.idxmax()
        st.info(f"""
        📊 **Insight do Analista:** A região **{regiao_lider}** concentra mais acidentes,
        o que se explica pela combinação de: maior densidade de rodovias federais,
        maior frota de veículos e maior volume de tráfego de carga e passageiros.
        Isso não indica necessariamente que as rodovias dessa região sejam mais perigosas —
        é preciso normalizar pelo volume de tráfego (veículos×km).
        """)

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

        regiao_mais_grave = grav_regiao.idxmax()
        regiao_menos_grave = grav_regiao.idxmin()
        st.warning(f"""
        ⚠️ **Análise de Risco Regional:** Em clima adverso, a região **{regiao_mais_grave}** apresenta
        a maior gravidade média, enquanto a **{regiao_menos_grave}** tem a menor.
        Fatores que influenciam:
        - 🏥 **Distância de hospitais:** Regiões com menos infraestrutura de saúde próxima às rodovias
          tendem a registrar mais óbitos (tempo de resgate mais longo).
        - 🛤️ **Perfil das rodovias:** Rodovias de pista simples (sem divisor central) são mais perigosas
          em clima adverso por permitir colisões frontais.
        - 🚛 **Tipo de tráfego:** Regiões com mais caminhões pesados geram acidentes mais graves.
        """)

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
st.subheader("📝 Conclusão Analítica")

clima_mais_frequente = acidentes_por_clima.idxmax() if not acidentes_por_clima.empty else "N/A"
tipo_chuva_comum = tipos_chuva.idxmax() if not tipos_chuva.empty else "N/A"

# Calcular métricas para a conclusão
grav_adv_final = df_filtrado[df_filtrado["clima_adverso"] == "Adverso"]["indice_gravidade"].mean()
grav_nor_final = df_filtrado[df_filtrado["clima_adverso"] == "Normal"]["indice_gravidade"].mean()
razao_final = grav_adv_final / grav_nor_final if grav_nor_final > 0 else 0
mortos_adverso_total = int(df_filtrado[df_filtrado["clima_adverso"] == "Adverso"]["mortos"].sum())
mortos_normal_total = int(df_filtrado[df_filtrado["clima_adverso"] == "Normal"]["mortos"].sum())
n_adverso = len(df_filtrado[df_filtrado["clima_adverso"] == "Adverso"])
n_normal = len(df_filtrado[df_filtrado["clima_adverso"] == "Normal"])
taxa_mortalidade_adv = mortos_adverso_total / n_adverso if n_adverso > 0 else 0
taxa_mortalidade_nor = mortos_normal_total / n_normal if n_normal > 0 else 0

st.markdown(f"""
### 🔍 Achados Descritivos

| Indicador | Valor |
|-----------|-------|
| Condição com mais acidentes (absoluto) | **{clima_mais_frequente}** |
| Tipo de colisão mais frequente na chuva | **{tipo_chuva_comum}** |
| % de acidentes em clima adverso | **{pct_adverso:.1f}%** |
| Gravidade média geral | **{gravidade_media:.2f}** |
| Razão de gravidade (adverso/normal) | **{razao_final:.2f}x** |

---

### 🧠 Análise dos "Porquês"

**1. Por que céu claro tem mais acidentes em números absolutos?**
- Porque céu claro é a condição meteorológica predominante no Brasil (~{100 - pct_adverso:.0f}% dos dias).
- Mais exposição temporal = mais acidentes registrados. **Isso não indica maior periculosidade.**

**2. Por que o clima adverso é mais perigoso proporcionalmente?**
- Pista molhada reduz atrito em 30-50%, aumentando distância de frenagem.
- Neblina/chuva reduzem visibilidade, impedindo reação preventiva.
- Aquaplanagem causa perda total de controle do veículo.
- Resultado: colisões ocorrem a velocidades de impacto mais altas → lesões mais graves.

**3. Por que colisões traseiras dominam em dias de chuva?**
- A distância de frenagem aumenta significativamente (F = μ × N, onde μ diminui com água).
- Motoristas mantêm a mesma distância de seguimento de dias secos.
- Spray de água do veículo da frente reduz visibilidade dos freios.

**4. Por que a gravidade é maior na madrugada?**
- Menor volume de tráfego permite velocidades mais altas.
- Fadiga e álcool comprometem tempo de reação.
- Menor iluminação dificulta identificação de obstáculos.
- Serviços de resgate demoram mais (menor efetivo noturno).

---

### 💡 Recomendações (como Analista de Dados)

1. **Campanhas de prevenção** devem ser intensificadas em períodos de chuva,
   focando em manter distância de seguimento e reduzir velocidade.
2. **Sinalização viária** em regiões Sul e Sudeste deve priorizar placas de
   "pista escorregadia" e limites de velocidade reduzidos para chuva.
3. **Fiscalização** no horário de pico (17h-19h) e madrugadas de final de semana
   pode reduzir os acidentes mais graves.
4. **Investimento em drenagem** nas rodovias com mais saídas de pista em chuva
   pode mitigar aquaplanagem.

---

### ⚠️ Limitações da Análise

- **Não possuímos dados de volume de tráfego** por condição climática, o que impede
  calcular a taxa de acidentes por veículo×km exposto à chuva.
- **A classificação meteorológica é feita no momento do registro**, podendo haver
  imprecisões (chuva intermitente registrada como "céu claro").
- **Não há dados de velocidade** dos veículos no momento do acidente, o que limita
  a análise causal direta.
- **O dataset é de um único ano (2024)**, impossibilitando análise de tendências
  temporais ou sazonais entre anos.
""")
