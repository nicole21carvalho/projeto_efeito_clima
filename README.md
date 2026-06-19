<h1 align="center"> O Efeito Clima nos Acidentes Rodoviários </h1>

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

## Sobre o Projeto

> **Pergunta central:** Como as condições meteorológicas impactam a gravidade e o tipo dos acidentes registrados em rodovias federais brasileiras?

Este projeto analisa **73.156 registros de acidentes** (2024) da Polícia Rodoviária Federal (PRF), investigando a relação entre clima e acidentes de trânsito através de uma interface interativa construída com Streamlit. A análise vai além da contagem de ocorrências, aplicando **normalização proporcional** e **razões de risco** para explicar os padrões encontrados.

---

## Tecnologias

| Tecnologia | Uso no projeto |
|:---:|---|
| **Python** | Linguagem principal |
| **Pandas** | Manipulação, limpeza e agregação de dados |
| **Numpy** | Operações numéricas, vetorização e criação de features |
| **Matplotlib** | Geração de gráficos estatísticos (barras, linhas, histogramas) |
| **Streamlit** | Interface web interativa com filtros e abas |

---

## Como Executar

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

## O que a Aplicação Mostra

A interface possui **4 abas temáticas**, **4 filtros interativos** e **13 visualizações** com insights analíticos:

| Aba | Conteúdo | Análise |
|---|---|---|
| 🌦️ **Clima** | Top 10 condições · Gravidade normalizada · Chuva vs Céu Claro | Explica por que céu claro lidera (frequência, não perigo) |
| ⚠️ **Gravidade** | Gravidade por clima · Razão de risco · Histograma de distribuição | Quantifica o risco proporcional do clima adverso |
| 🕐 **Temporal** | Por hora · Gravidade por hora · Por dia da semana | Identifica paradoxo volume vs gravidade (madrugada) |
| 🗺️ **Geográfico** | Top 10 UFs · Taxa adverso/total · Gravidade por região | Normaliza por frequência, revela regiões de maior risco |

**Filtros disponíveis:** Estado (UF) · Condição meteorológica · Ano · Período do dia

**Diferencial analítico:** Cada gráfico acompanha um bloco de "Insight do Analista" que explica:
- **O que** o gráfico mostra
- **Por que** o padrão ocorre (causa raiz)
- **O que** isso significa para a segurança viária

---

## Metodologia de Tratamento

O pipeline de dados segue 5 etapas:

```
CSV (dados brutos) → Limpeza → Engenharia de Features → Análise Visual → Conclusão Analítica
```

### Limpeza realizada (Pandas)
- ✅ Remoção de duplicatas
- ✅ Tratamento de valores nulos (texto → "Não informado", numéricos → 0)
- ✅ Padronização de colunas (snake_case sem acentos via `unicodedata`)
- ✅ Correção de encoding corrompido (latin1 ↔ UTF-8, com fallback manual)
- ✅ Conversão de tipos (`to_datetime`, `to_numeric` com `errors="coerce"`)
- ✅ Validação de colunas essenciais com feedback ao usuário

### Features criadas (Numpy + Pandas)

| Feature | Fórmula / Lógica | Justificativa analítica |
|---|---|---|
| `clima_adverso` | "Adverso" se chuva/garoa/neblina/vento/granizo | Permite comparação binária direta entre grupos |
| `total_feridos` | `feridos_leves + feridos_graves` | Simplifica agregações de vítimas |
| `indice_gravidade` | `mortos×3 + graves×2 + leves×1` | Pondera severidade (óbito pesa 3x mais que ferimento leve) |
| `periodo_dia` | `pd.cut` em 4 faixas horárias | Revela padrões de risco por turno |
| `regiao` | Mapeamento UF → Região (dict) | Agrupamento geográfico para análise macro |
| `dia_semana_num` | 0 (seg) a 6 (dom) | Permite ordenação e análise cíclica |

---

## Principais Achados

### Achados Descritivos
- A maioria dos acidentes ocorre em **céu claro** — porque é a condição predominante (~70% dos dias)
- O **clima adverso** representa ~20-30% dos acidentes, mas com **gravidade proporcionalmente maior**
- Em dias de chuva, **colisões traseiras e saídas de pista** são desproporcionalmente frequentes

### Explicações Analíticas (os "Porquês")
| Padrão observado | Causa provável |
|---|---|
| Céu claro lidera em volume | Condição mais frequente no Brasil — mais exposição temporal |
| Clima adverso = mais grave | Pista molhada reduz atrito 30-50%, colisões a velocidades mais altas |
| Colisões traseiras na chuva | Distância de frenagem aumenta + spray reduz visibilidade |
| Saídas de pista na chuva | Aquaplanagem (perda de contato pneu-asfalto) |
| Pico 17-19h em volume | Horário de rush + redução de luminosidade |
| Madrugada mais grave | Velocidade alta + álcool + fadiga + menos resgate |

### Recomendações
1. Campanhas de prevenção focadas em períodos chuvosos (distância de seguimento)
2. Sinalização dinâmica de "pista escorregadia" em regiões Sul/Sudeste
3. Fiscalização intensificada 17h-19h e madrugadas de fim de semana
4. Investimento em drenagem nas rodovias com mais saídas de pista

### Limitações
- Sem dados de volume de tráfego por condição (impossível calcular taxa por veículo×km)
- Classificação meteorológica feita no momento do registro (possíveis imprecisões)
- Sem dados de velocidade no momento do acidente
- Dataset de um único ano (2024)

---

## Estrutura do Projeto

```
projeto_efeito_clima/
├── app.py                              # Código principal (650+ linhas, modular)
├── acidentes_prf.csv                   # Dataset da PRF (73.156 registros)
├── requirements.txt                    # Dependências do projeto
├── Relatorio_Projeto_Efeito_Clima.md   # Relatório completo (exportável para PDF)
├── Relatorio_Projeto_Efeito_Clima.pdf  # Relatório em PDF
└── README.md                           # Este arquivo
```

---

## Possíveis Erros

| Erro | Solução |
|---|---|
| `No such file: acidentes_prf.csv` | Verifique se o CSV está na mesma pasta do `app.py` |
| `streamlit não é reconhecido` | Use `python -m streamlit run app.py` |
| Caracteres quebrados (`C�u Claro`) | Menu ⋮ → Clear cache → Rerun |
