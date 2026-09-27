# OpenF1 Data Explorer

Aplicação web interativa construída com **Python + Streamlit** para explorar dados de Fórmula 1 armazenados em um banco **MongoDB**.

O projeto é composto por dois módulos independentes: um **coletor de dados** que busca informações diretamente da [API OpenF1](https://openf1.org/) e as persiste no banco, e um **dashboard interativo** que permite visualizar e comparar o desempenho dos pilotos sessão por sessão.

---

## Funcionalidades

### Coletor (`f1_data_collector.py`)

- Busca todas as sessões de um ano na API OpenF1 e salva na coleção `sessions`
- Para cada sessão, coleta os dados de pilotos (`drivers`) e voltas (`laps`)
- Usa `upsert` para sessões (evita duplicatas ao rodar mais de uma vez) e `delete + insert` para pilotos e voltas
- Trata erros de rate limit (HTTP 429) por sessão sem abortar a coleta inteira

### Dashboard (`streamlit_app.py`)

- **Filtros dinâmicos** na barra lateral: ano, tipo de sessão (`Race`, `Qualifying`, `Practice`) e sessão específica
- **Métricas de contexto** da sessão selecionada: País, Circuito e Data
- **Seleção de múltiplos pilotos** com `st.multiselect`, pré-selecionando os dois primeiros por padrão
- **Gráfico de tempo por volta** (`lap_duration × lap_number`) com linha por piloto e marcadores de saída dos boxes
- **Cores das equipes** aplicadas automaticamente nos gráficos quando disponíveis no banco
- **Estatísticas por piloto**: melhor volta, média e desvio padrão em tabela comparativa
- **Gráfico de setores** (S1, S2, S3) em painéis facetados por setor
- **Tabela de dados brutos** expansível com todas as colunas relevantes
- **Exportação em CSV** compatível com Excel (encoding UTF-8 com BOM)
- Cache de 5 minutos em todas as consultas ao banco para melhor desempenho

---

## Estrutura do projeto

```
.
├── f1_data_collector.py   # Script de coleta de dados via API OpenF1
├── streamlit_app.py       # Interface principal do dashboard (Streamlit)
├── db_utils.py            # Módulo de conexão e consultas ao MongoDB
├── requirements.txt       # Dependências Python
├── .env.example           # Modelo do arquivo de variáveis de ambiente
├── .gitignore             # Arquivos ignorados pelo Git
└── HANDOFF.md             # Registro do trabalho em equipe
```

---

## Pré-requisitos

- **Python 3.10+** instalado
- **MongoDB** rodando localmente (`localhost:27017`) ou URI de uma instância remota (ex: MongoDB Atlas)
- Conexão com a internet para executar o coletor

---

## Instalação e configuração

### 1. Criar o ambiente virtual e instalar dependências

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2. Configurar as variáveis de ambiente

Copie o arquivo de exemplo e edite com os seus valores:

```powershell
Copy-Item .env.example .env
```

Abra `.env` e ajuste conforme necessário:

```dotenv
MONGODB_URI=mongodb://localhost:27017   # URI do MongoDB
DB_NAME=openf1_data                    # Nome do banco de dados
BASE_URL=https://api.openf1.org/v1     # URL base da API (não altere)
ANO=2023                               # Ano a ser coletado pelo coletor
```

---

## Como usar

### Passo 1 — Coletar os dados

Execute o script coletor para popular o banco com os dados do ano configurado em `.env`:

```powershell
.\venv\Scripts\python.exe f1_data_collector.py
```

O script imprime o progresso no terminal em três etapas:

```
[1/3] Buscando sessões...
[2/3] Salvando sessões...
[3/3] Coletando pilotos e voltas...
```

> **Nota:** A API OpenF1 possui limite de requisições (rate limit). Se sessões retornarem erro 429, o coletor registra o erro e continua com a próxima sessão. Basta rodar o script novamente para completar as sessões que falharam.

**Resultado esperado ao final da coleta de 2023:**
```
Sessões no MongoDB: 118
Pilotos no MongoDB: ~632
Voltas no MongoDB: ~17822
```

### Passo 2 — Iniciar o dashboard

```powershell
.\venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

O Streamlit exibirá a URL no terminal. Abra no navegador:

```
Local URL: http://localhost:8501
```

---

## Banco de dados

O banco `openf1_data` (configurável via `DB_NAME`) utiliza três coleções:

| Coleção | Descrição | Campos principais |
|---|---|---|
| `sessions` | Informações sobre cada sessão de corrida | `session_key`, `session_name`, `session_type`, `year`, `country_name`, `circuit_short_name`, `date_start` |
| `drivers` | Pilotos por sessão | `session_key`, `driver_number`, `full_name`, `name_acronym`, `team_name`, `team_colour` |
| `laps` | Dados de volta por piloto/sessão | `session_key`, `driver_number`, `lap_number`, `lap_duration`, `duration_sector_1/2/3`, `is_pit_out_lap` |

---

## Dependências

| Pacote | Versão | Uso |
|---|---|---|
| `streamlit` | 1.35.0 | Framework do dashboard |
| `pymongo` | 4.6.3 | Conexão com MongoDB |
| `python-dotenv` | 1.0.1 | Carregamento do `.env` |
| `pandas` | 2.2.2 | Manipulação dos dados em DataFrame |
| `plotly` | 5.22.0 | Gráficos interativos |
| `requests` | (latest) | Requisições HTTP à API OpenF1 |

---

## Fluxo de dados

```
API OpenF1  →  f1_data_collector.py  →  MongoDB (openf1_data)
                                               ↓
                                       db_utils.py (consultas)
                                               ↓
                                       streamlit_app.py (dashboard)
```

---

## Caso de uso documentado

O documento da prática descreve a análise do **GP da Itália 2023** (`session_key = 9159`) como referência:

1. Selecione o ano **2023** e o tipo **Race** na sidebar
2. Escolha **Italian Grand Prix – Italy** no menu de sessões
3. Selecione **LEC** e **SAI** (Leclerc e Sainz) no multiselect de pilotos
4. Observe o gráfico de volta a volta — tempos na faixa de 85–95 s confirmam ingestão correta
5. Os picos no gráfico indicam voltas de saída dos boxes (marcadores em amarelo)

---

> Dados fornecidos pela [API OpenF1](https://openf1.org/) — gratuita e aberta.
> Projeto desenvolvido para a **Prática 04 – Manipulação dos Dados em Banco MongoDB**.
