# 🌧️ O Efeito Clima nos Acidentes Rodoviários

Este projeto foi desenvolvido em Python com Streamlit, Pandas, Numpy, Matplotlib e Scikit-learn.
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

Caso o arquivo `requirements.txt` ainda não exista, crie um arquivo com esse nome e coloque dentro dele:

```text
streamlit
pandas
numpy
matplotlib
scikit-learn
```

Depois execute novamente:

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

## 10. Objetivo da análise

O projeto busca responder à seguinte pergunta:

**Como as condições meteorológicas impactam a gravidade e o tipo dos acidentes registrados em rodovias federais brasileiras?**

A aplicação permite analisar:

* Total de acidentes
* Total de mortos
* Total de feridos
* Percentual de acidentes em clima adverso
* Gravidade média dos acidentes
* Acidentes por condição meteorológica
* Tipos de acidente em dias de chuva
* Acidentes por horário
* Estados com mais acidentes em clima adverso
* Modelo preditivo opcional com Scikit-learn

---

## 11. Tecnologias utilizadas

* Python
* Streamlit
* Pandas
* Numpy
* Matplotlib
* Scikit-learn

---

## 12. Comando principal para rodar

Resumo final:

```bash
git clone LINK_DO_REPOSITORIO
cd projeto_efeito_clima
python -m venv venv
venv\Scripts\Activate
pip install -r requirements.txt
python -m streamlit run app.py
```
