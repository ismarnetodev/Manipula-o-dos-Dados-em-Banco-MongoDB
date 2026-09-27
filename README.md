# OpenF1 Data Explorer

Aplicação web interativa construída com **Streamlit** para explorar dados de Fórmula 1 armazenados no MongoDB (banco `openf1_data`).

## Estrutura do projeto

```
.
├── streamlit_app.py   # Interface principal (Streamlit)
├── db_utils.py        # Módulo de conexão e consultas ao MongoDB
├── requirements.txt   # Dependências Python
├── .env.example       # Modelo do arquivo de configuração
├── .gitignore
└── HANDOFF.md         # Instruções para o próximo membro da equipa
```

## Como rodar

1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Crie o arquivo `.env` a partir do exemplo:
   ```bash
   cp .env.example .env
   # edite .env com a sua URI do MongoDB
   ```

3. Suba a aplicação:
   ```bash
   streamlit run streamlit_app.py
   ```

## Banco de dados esperado

O banco `openf1_data` deve ter as coleções:
- `sessions` – informações sobre as sessões de corrida
- `drivers` – pilotos por sessão
- `laps` – dados de voltas por piloto/sessão

> Os dados são populados pelo script coletor (`f1_data_collector.py`) descrito na Prática 03.
