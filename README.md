# OpenF1 Data Explorer

Aplicação web interativa construída com **Streamlit** para explorar dados de Fórmula 1 armazenados no MongoDB (banco `openf1_data`).

## Funcionalidades

- Filtros por ano, tipo de sessão e sessão específica.
- Comparação de tempos de volta e setores entre pilotos.
- Estatísticas por piloto: melhor volta, média e desvio padrão.
- Destaque para voltas de saída dos boxes e cores de equipe quando disponíveis.
- Tabela de voltas e exportação dos dados filtrados para CSV.

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

## Como executar no Windows PowerShell

Os comandos abaixo usam diretamente o Python do ambiente virtual, então não é necessário ativar `venv` no PowerShell.

1. Crie o ambiente virtual e instale as dependências:
   ```powershell
   py -m venv venv
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. Crie `.env` a partir do modelo e informe sua URI do MongoDB:
   ```powershell
   Copy-Item .env.example .env
   ```

3. Inicie a aplicação:
   ```powershell
   .\venv\Scripts\python.exe -m streamlit run streamlit_app.py
   ```

O Streamlit exibirá a URL local no terminal.

## Banco de dados esperado

O banco `openf1_data` deve ter as coleções:
- `sessions` – informações sobre as sessões de corrida
- `drivers` – pilotos por sessão
- `laps` – dados de voltas por piloto/sessão

> Os dados são populados pelo script coletor (`f1_data_collector.py`) descrito na Prática 03.
