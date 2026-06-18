# 🌧️ O Efeito Clima nos Acidentes Rodoviários

Este projeto foi desenvolvido em Python com Streamlit, Pandas, Numpy e Matplotlib.
O objetivo é analisar como as condições meteorológicas influenciam a frequência, o tipo e a gravidade dos acidentes em rodovias federais brasileiras.

---

## 1. Pré-requisitos

Antes de executar o projeto, é necessário ter instalado no computador:

* Python 3.10 ou superior
* Visual Studio Code
* Git
* Extensão Python no VS Code

Para verificar se o Python está instalado, abra o terminal e execute:

```bash
python --version
```

ou:

```bash
py --version
```

Para verificar se o Git está instalado:

```bash
git --version
```

---

## 2. Clonar o projeto do GitHub

No GitHub, copie o link do repositório.

Depois, abra o terminal ou o PowerShell e execute:

```bash
git clone LINK_DO_REPOSITORIO
```

Exemplo:

```bash
git clone https://github.com/seu-usuario/projeto_efeito_clima.git
```

Depois entre na pasta do projeto:

```bash
cd projeto_efeito_clima
```

---

## 3. Abrir o projeto no VS Code

Com a pasta do projeto aberta no terminal, execute:

```bash
code .
```

Isso abrirá o projeto diretamente no Visual Studio Code.

Caso o comando `code .` não funcione, abra o VS Code manualmente e vá em:

```text
File > Open Folder > selecione a pasta projeto_efeito_clima
```

---

## 4. Verificar os arquivos do projeto

A pasta do projeto deve conter pelo menos os seguintes arquivos:

```text
projeto_efeito_clima/
│
├── app.py
├── acidentes_prf.csv
├── requirements.txt
└── README.md
```

O arquivo `acidentes_prf.csv` precisa estar na mesma pasta do `app.py`.

---

## 5. Criar o ambiente virtual

No terminal do VS Code, execute:

```bash
python -m venv venv
```

Depois ative o ambiente virtual.

No Windows PowerShell:

```bash
venv\Scripts\Activate
```

No CMD:

```bash
venv\Scripts\activate.bat
```

No Linux ou Mac:

```bash
source venv/bin/activate
```

Quando o ambiente estiver ativo, aparecerá algo parecido com:

```text
(venv)
```

no início da linha do terminal.

---

## 6. Instalar as dependências

Com o ambiente virtual ativado, instale as bibliotecas necessárias:

```bash
pip install -r requirements.txt
```

---

## 7. Executar o projeto

Com tudo instalado, execute:

```bash
python -m streamlit run app.py
```

O Streamlit abrirá automaticamente no navegador.

Caso apareça uma pergunta solicitando e-mail, basta pressionar `Enter` sem digitar nada.

---

## 8. Possíveis erros e soluções

### Erro: `No such file or directory: acidentes_prf.csv`

Esse erro significa que o arquivo CSV não está na mesma pasta do `app.py`.

Solução:

* Verifique se o arquivo `acidentes_prf.csv` existe.
* Verifique se ele está dentro da pasta do projeto.
* Verifique se o nome está exatamente como:

```text
acidentes_prf.csv
```

---

### Erro: `streamlit não é reconhecido`

Execute o projeto usando:

```bash
python -m streamlit run app.py
```

Se ainda não funcionar, instale o Streamlit:

```bash
pip install streamlit
```

---

### Erro com acentos ou palavras quebradas

Se aparecerem palavras como `C�u Claro` ou `Colis�o`, limpe o cache do Streamlit:

```text
Menu ⋮ > Clear cache > Rerun
```

Depois execute novamente o projeto.

---

## 9. Encerrar o projeto

Para parar o Streamlit, volte ao terminal e pressione:

```bash
Ctrl + C
```

---

## 10. Metodologia de Tratamento dos Dados

O pipeline de limpeza e preparação segue as seguintes etapas:

### 10.1 Carregamento
O dataset é carregado com `pandas.read_csv()` usando encoding `latin1` e separador `;`,
padrão dos dados abertos da PRF.

### 10.2 Remoção de duplicatas
Registros duplicados são identificados e removidos com `DataFrame.drop_duplicates()`.
A quantidade de duplicatas removidas é exibida na interface.

### 10.3 Padronização de colunas
Os nomes das colunas são convertidos para snake_case minúsculo sem acentos,
garantindo consistência independente da formatação original.

### 10.4 Tratamento de valores nulos
- **Colunas de texto** (UF, tipo de acidente, condição meteorológica): valores nulos
  são preenchidos com "Não informado".
- **Colunas numéricas** (mortos, feridos leves, feridos graves, veículos): valores nulos
  ou não numéricos são convertidos para 0.
- As estatísticas de nulos tratados são exibidas na interface.

### 10.5 Correção de encoding
O CSV da PRF contém textos corrompidos por conversões de encoding (latin1 ↔ UTF-8).
A função `corrigir_encoding_texto()` aplica recodificação automática e correções manuais
para os casos mais comuns.

### 10.6 Engenharia de features
Novas colunas criadas a partir dos dados brutos:

| Feature | Descrição | Justificativa |
|---------|-----------|---------------|
| `clima_adverso` | "Adverso" ou "Normal" | Permite comparação direta entre climas favoráveis e desfavoráveis |
| `total_feridos` | `feridos_leves + feridos_graves` | Simplifica análise de vítimas |
| `indice_gravidade` | `mortos×3 + graves×2 + leves×1` | Índice ponderado que reflete a severidade real |
| `periodo_dia` | Madrugada/Manhã/Tarde/Noite | Permite análise por faixa horária |
| `regiao` | Norte/Nordeste/Centro-Oeste/Sudeste/Sul | Análise geográfica por região |
| `dia_semana_num` | 0 (segunda) a 6 (domingo) | Permite análise de padrões semanais |

---

## 11. Objetivo da análise

O projeto busca responder à seguinte pergunta:

**Como as condições meteorológicas impactam a gravidade e o tipo dos acidentes registrados em rodovias federais brasileiras?**

A aplicação permite analisar:

* Total de acidentes, mortos e feridos
* Percentual de acidentes em clima adverso
* Gravidade média dos acidentes
* Acidentes por condição meteorológica
* Tipos de acidente em dias de chuva
* Acidentes por horário e dia da semana
* Comparativo de gravidade: clima adverso vs normal
* Distribuição por região e estados
* Gravidade média por região em clima adverso

---

## 12. Tecnologias utilizadas

* Python
* Streamlit
* Pandas
* Numpy
* Matplotlib

---

## 13. Comando principal para rodar

Resumo final:

```bash
git clone LINK_DO_REPOSITORIO
cd projeto_efeito_clima
python -m venv venv
venv\Scripts\Activate
pip install -r requirements.txt
python -m streamlit run app.py
```
