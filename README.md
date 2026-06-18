# 🌧️ O Efeito Clima nos Acidentes Rodoviários

<p align="center">
  <b>Análise de Dados e Solução de Problemas com Python</b><br>
  Disciplina: Novas Tecnologias Python<br>
  Professor: Lucas d'Andurain Ramos Bitar
</p>

<p align="center">
  <b>Integrantes:</b><br>
  Pedro Braga de Lima · Maria Clara Paiva Oliveira Camelo<br>
  Maria Clara Ferreira Dos Santos · Nicole Reinaldo De Carvalho
</p>

---

## 📌 Sobre o Projeto

> **Pergunta central:** Como as condições meteorológicas impactam a gravidade e o tipo dos acidentes registrados em rodovias federais brasileiras?

Este projeto analisa **73.156 registros de acidentes** (2024) da Polícia Rodoviária Federal (PRF), investigando a relação entre clima e acidentes de trânsito através de uma interface interativa construída com Streamlit.

---

## 🛠️ Tecnologias

| Tecnologia | Uso no projeto |
|:---:|---|
| **Python** | Linguagem principal |
| **Pandas** | Manipulação e limpeza de dados |
| **Numpy** | Operações numéricas e criação de features |
| **Matplotlib** | Geração de gráficos estatísticos |
| **Streamlit** | Interface web interativa |

---

## 🚀 Como Executar

```bash
# 1. Clone o repositório
git clone <URL_DO_REPOSITORIO>
cd projeto_efeito_clima

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\Activate        # Windows PowerShell
# source venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a aplicação
python -m streamlit run app.py
```

> Se pedir e-mail, pressione **Enter** sem digitar nada.

---

## 📊 O que a Aplicação Mostra

A interface possui **4 abas temáticas**, **4 filtros interativos** e **9 gráficos**:

| Aba | Conteúdo |
|---|---|
| 🌦️ **Clima** | Top 10 condições meteorológicas · Tipos de colisão em dias de chuva |
| ⚠️ **Gravidade** | Gravidade média por clima · Comparativo adverso vs normal |
| 🕐 **Temporal** | Acidentes por hora do dia · Acidentes por dia da semana |
| 🗺️ **Geográfico** | Top 10 estados · Acidentes por região · Gravidade por região |

**Filtros disponíveis:** Estado (UF) · Condição meteorológica · Ano · Período do dia

---

## 🔧 Metodologia de Tratamento

O pipeline de dados segue 5 etapas:

```
CSV (dados brutos) → Limpeza → Engenharia de Features → Visualização → Conclusão
```

### Limpeza realizada
- ✅ Remoção de duplicatas
- ✅ Tratamento de valores nulos (texto e numéricos)
- ✅ Padronização de colunas (snake_case sem acentos)
- ✅ Correção de encoding corrompido (latin1 ↔ UTF-8)
- ✅ Conversão de tipos (datas, numéricos)

### Features criadas

| Feature | Fórmula | Por quê? |
|---|---|---|
| `clima_adverso` | Adverso / Normal | Comparação direta entre climas |
| `total_feridos` | leves + graves | Simplifica análise de vítimas |
| `indice_gravidade` | mortos×3 + graves×2 + leves×1 | Reflete severidade real |
| `periodo_dia` | Madrugada / Manhã / Tarde / Noite | Padrões por faixa horária |
| `regiao` | Norte / NE / CO / SE / Sul | Análise geográfica |
| `dia_semana_num` | 0 (seg) a 6 (dom) | Padrões semanais |

---

## 📝 Conclusão

- A maioria dos acidentes ocorre em **céu claro** (condição mais frequente)
- Porém, o **clima adverso apresenta gravidade proporcionalmente maior**
- Em dias de chuva, **colisões traseiras e saídas de pista** são mais frequentes
- **A chuva impacta tanto o tipo quanto a gravidade** dos acidentes

---

## 📁 Estrutura do Projeto

```
projeto_efeito_clima/
├── app.py                              # Código principal da aplicação
├── acidentes_prf.csv                   # Dataset da PRF (73.156 registros)
├── requirements.txt                    # Dependências do projeto
├── Relatorio_Projeto_Efeito_Clima.pdf  # Relatório auxiliar
└── README.md                           # Este arquivo
```

---

## ⚠️ Possíveis Erros

| Erro | Solução |
|---|---|
| `No such file: acidentes_prf.csv` | Verifique se o CSV está na mesma pasta do `app.py` |
| `streamlit não é reconhecido` | Use `python -m streamlit run app.py` |
| Caracteres quebrados (`C�u Claro`) | Menu ⋮ → Clear cache → Rerun |
