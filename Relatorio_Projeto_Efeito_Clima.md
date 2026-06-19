<h1 align="center"> Relatório: O Efeito Clima nos Acidentes Rodoviários </h1>

<p align="center">
  <b>Análise de Dados e Solução de Problemas com Python</b><br>
  Disciplina: Novas Tecnologias Python · Professor: Lucas d'Andurain Ramos Bitar
</p>

<p align="center">
  <b>Integrantes:</b><br>
  Pedro Braga de Lima · Maria Clara Paiva Oliveira Camelo<br>
  Maria Clara Ferreira Dos Santos · Nicole Reinaldo De Carvalho
</p>

---

## 1. Introdução ao Problema

### 1.1 Contexto

O Brasil possui uma das maiores malhas rodoviárias do mundo, com mais de 75 mil quilômetros de rodovias federais. A Polícia Rodoviária Federal (PRF) registra dezenas de milhares de acidentes anualmente, resultando em perdas humanas e econômicas significativas. Compreender os fatores que influenciam esses acidentes é essencial para políticas públicas de prevenção.

### 1.2 Pergunta de Pesquisa

> **Como as condições meteorológicas impactam a gravidade e o tipo dos acidentes registrados em rodovias federais brasileiras?**

Esta pergunta se desdobra em subquestões analíticas:
- Por que a maioria dos acidentes ocorre em céu claro?
- O clima adverso realmente aumenta o risco de acidentes mais graves?
- Quais tipos de colisão são mais afetados pela chuva e por quê?
- Existem padrões temporais e geográficos que amplificam o efeito do clima?

### 1.3 Dataset Utilizado

| Característica | Detalhe |
|---|---|
| **Fonte** | Dados Abertos da PRF (Polícia Rodoviária Federal) |
| **Período** | Ano de 2024 |
| **Registros** | 73.156 acidentes |
| **Variáveis** | UF, tipo de acidente, condição meteorológica, mortos, feridos leves/graves, horário, data, dia da semana, entre outras |
| **Formato** | CSV com separador `;` e encoding `latin1` |

---

## 2. Metodologia

### 2.1 Pipeline de Dados

```
CSV (dados brutos) → Limpeza → Engenharia de Features → Análise Visual → Conclusão Analítica
```

### 2.2 Etapa 1: Carregamento (Pandas)

- Leitura com `pd.read_csv()` especificando `sep=";"` e `encoding="latin1"`
- Uso de `@st.cache_data` para otimizar recarregamentos no Streamlit
- Validação de existência do arquivo com feedback ao usuário

### 2.3 Etapa 2: Limpeza e Preparação (Pandas + Numpy)

| Ação | Ferramenta | Justificativa |
|---|---|---|
| Remoção de duplicatas | `df.drop_duplicates()` | Evita contagem duplicada de ocorrências |
| Padronização de colunas | `unicodedata` + `re` | Colunas em snake_case sem acentos para consistência |
| Tratamento de nulos (texto) | `fillna("Não informado")` | Preserva registros sem perder dados válidos |
| Tratamento de nulos (numéricos) | `pd.to_numeric(...).fillna(0)` | Zero mortos/feridos = nenhum registro de vítima |
| Correção de encoding | Recodificação `latin1 → UTF-8` + mapa manual | Dados da PRF vêm com encoding corrompido |
| Conversão de datas | `pd.to_datetime(errors="coerce")` | Permite extração de hora, mês e ano |
| Extração temporal | `.dt.hour`, `.dt.year`, `.dt.month` | Habilita análises temporais |

**Estatísticas da limpeza** (exibidas na interface):
- Duplicatas removidas
- Nulos de texto preenchidos
- Nulos numéricos preenchidos
- Datas inválidas identificadas

### 2.4 Etapa 3: Engenharia de Features (Numpy + Pandas)

| Feature criada | Implementação | Propósito analítico |
|---|---|---|
| `clima_adverso` | `np.where(condição ∈ [chuva, garoa, neblina, vento, granizo], "Adverso", "Normal")` | Classificação binária para comparação direta de grupos |
| `total_feridos` | `feridos_leves + feridos_graves` | Métrica unificada de vítimas não fatais |
| `indice_gravidade` | `mortos×3 + feridos_graves×2 + feridos_leves×1` | Índice ponderado que reflete severidade real (óbito pesa 3x) |
| `periodo_dia` | `pd.cut(hora, bins=[-1,5,11,17,23])` | Segmentação em Madrugada/Manhã/Tarde/Noite |
| `regiao` | Mapeamento `UF → Região` via dicionário | Agrupamento para análise geográfica macro |
| `dia_semana_num` | Mapeamento textual → 0-6 | Permite ordenação e correlação temporal |

### 2.5 Etapa 4: Interface e Visualização (Streamlit + Matplotlib)

A interface foi construída com os seguintes componentes:

**Filtros interativos (sidebar):**
- Estado (UF) — multiselect
- Condição meteorológica — multiselect
- Ano — multiselect
- Período do dia — multiselect

**Indicadores gerais (métricas):**
- Total de acidentes, mortos, feridos, % clima adverso, gravidade média

**4 abas temáticas com 13 visualizações:**

| Aba | Gráficos | Tipo de análise |
|---|---|---|
| Clima | Top 10 condições + Gravidade normalizada + Comparação Chuva vs Céu Claro | Proporcional (taxa, não contagem) |
| Gravidade | Gravidade por clima + Razão de risco + Histograma de distribuição | Risco quantificado |
| Temporal | Acidentes por hora + Gravidade por hora + Acidentes por dia | Padrões cíclicos |
| Geográfico | Top 10 UFs + Taxa adverso/total + Gravidade por região | Normalizada por frequência |

**Diferencial:** Cada gráfico é acompanhado de um bloco "Insight do Analista" que contextualiza o que o dado mostra, por que o padrão ocorre e o que isso significa.

---

## 3. Resultados Visuais

### 3.1 Aba Clima: Contagem vs Proporção

**Achado 1:** Céu claro lidera em número absoluto de acidentes (~70% do total).

**Explicação:** Céu claro é a condição meteorológica predominante no Brasil. Como a maioria dos dias apresenta essa condição, naturalmente a maior parte dos acidentes é registrada sob ela. **Isso não indica maior periculosidade** — indica maior exposição temporal.

**Achado 2:** Ao normalizar pela frequência (gravidade média por condição), condições adversas apresentam índices de gravidade superiores à média geral.

**Achado 3:** Em dias de chuva, colisões traseiras e saídas de pista são desproporcionalmente mais frequentes comparadas a céu claro (análise proporcional %).

**Por quê:**
- Pista molhada reduz o coeficiente de atrito em 30-50%, aumentando a distância de frenagem
- Aquaplanagem causa perda total de controle direcional
- Spray de água reduz visibilidade dos freios do veículo à frente

### 3.2 Aba Gravidade: Razão de Risco

**Achado 4:** A razão de gravidade (adverso/normal) demonstra que cada acidente em clima adverso é proporcionalmente mais grave que em clima normal.

**Achado 5:** O histograma de distribuição revela que acidentes em clima adverso possuem uma "cauda" mais pesada à direita (maior proporção de eventos de alta gravidade).

**Por quê:** Em clima adverso, a combinação de pista escorregadia + menor visibilidade + maior tempo de reação resulta em colisões com velocidade de impacto mais elevada, o que aumenta diretamente a severidade das lesões.

### 3.3 Aba Temporal: Paradoxo Volume vs Gravidade

**Achado 6:** O pico de acidentes ocorre entre 17h-19h (horário de rush).

**Achado 7:** Porém, a maior gravidade média ocorre na madrugada — quando há MENOS acidentes, mas mais letais.

**Por quê:**
- 17h-19h: maior fluxo de veículos + redução de luminosidade = mais colisões
- Madrugada: velocidade mais alta + fadiga + álcool + menos iluminação = menos acidentes, mas mais graves
- Finais de semana: menos volume total, porém gravidade elevada (viagens longas com fadiga)

### 3.4 Aba Geográfica: Análise Regional

**Achado 8:** Estados do Sul e Sudeste (PR, SC, MG, SP) lideram em acidentes com clima adverso tanto em números absolutos quanto proporcionalmente.

**Por quê:**
- Regime pluviométrico mais intenso e frequente nessas regiões
- Grande malha rodoviária federal (mais km de rodovias)
- Regiões serranas (SC, MG) combinam neblina frequente + curvas
- Maior frota de veículos e volume de tráfego

**Achado 9:** A gravidade média por região em clima adverso varia significativamente, sendo maior em regiões com menor infraestrutura de saúde próxima às rodovias (tempo de resgate mais longo).

---

## 4. Conclusão

### 4.1 Resposta à Pergunta Central

**"Como as condições meteorológicas impactam a gravidade e o tipo dos acidentes?"**

O clima adverso impacta os acidentes rodoviários de duas formas principais:

1. **No tipo de acidente:** A chuva aumenta desproporcionalmente colisões traseiras (distância de frenagem) e saídas de pista (aquaplanagem), alterando o perfil de acidentes comparado a dias de céu claro.

2. **Na gravidade:** Cada acidente em clima adverso é proporcionalmente mais grave que em clima normal. A razão de risco demonstra aumento significativo no índice de gravidade ponderado, na taxa de mortalidade e no número médio de feridos por ocorrência.

### 4.2 Insight Principal

O erro mais comum em análises superficiais é concluir que "céu claro é mais perigoso" porque apresenta mais acidentes em números absolutos. **A análise proporcional revela o oposto:** o clima adverso é o verdadeiro fator de risco, sendo que sua menor frequência mascara seu impacto real na gravidade dos acidentes.

### 4.3 Recomendações Baseadas nos Dados

| Recomendação | Baseada em |
|---|---|
| Campanhas de prevenção focadas em chuva (distância de seguimento) | Aumento de colisões traseiras em chuva |
| Sinalização dinâmica "pista escorregadia" em Sul/Sudeste | Alta proporção de acidentes adversos na região |
| Fiscalização intensificada 17h-19h e madrugadas de fim de semana | Picos de volume e de gravidade |
| Investimento em drenagem nas rodovias com mais saídas de pista | Aquaplanagem como causa de saídas |

### 4.4 Limitações

| Limitação | Impacto na análise |
|---|---|
| Sem dados de volume de tráfego por condição | Não é possível calcular taxa de acidentes por veículo×km exposto |
| Classificação meteorológica feita no momento do registro | Possíveis imprecisões (chuva intermitente → "céu claro") |
| Sem dados de velocidade dos veículos | Limita análise causal direta |
| Dataset de um único ano (2024) | Impossibilita análise de tendências entre anos |

---

## 5. Referências

- **Dados:** Portal de Dados Abertos da PRF — [dados.gov.br](https://dados.gov.br)
- **Streamlit:** [streamlit.io](https://streamlit.io)
- **Pandas:** [pandas.pydata.org](https://pandas.pydata.org)
- **Matplotlib:** [matplotlib.org](https://matplotlib.org)
- **Numpy:** [numpy.org](https://numpy.org)
