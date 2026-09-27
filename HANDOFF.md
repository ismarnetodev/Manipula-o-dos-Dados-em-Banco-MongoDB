# HANDOFF.md – OpenF1 Data Explorer

**Branch:** `branch-ismar`  
**Data:** 26/09/2026  
**Responsável até aqui:** Rejan  

---

## Estado atual do repositório

### O que já está feito (~50%)

| Arquivo | O que faz |
|---|---|
| `requirements.txt` | Todas as dependências definidas (streamlit, pymongo, plotly, pandas, python-dotenv) |
| `.env.example` | Modelo do arquivo de configuração com `MONGODB_URI` e `DB_NAME` |
| `.gitignore` | Ignora `.env`, `__pycache__`, `.venv` |
| `db_utils.py` | Módulo completo de conexão e consultas ao MongoDB |
| `streamlit_app.py` | Interface funcional com sidebar, métricas, seleção de pilotos, gráfico e tabela |
| `README.md` | Instruções de instalação e estrutura do projeto |

### Funcionalidades implementadas

- ✅ Conexão ao MongoDB via variável de ambiente (`.env`)
- ✅ Teste de conexão na inicialização da app (com `st.stop()` se falhar)
- ✅ Sidebar com filtro por **ano** (carregado dinamicamente da coleção `sessions`)
- ✅ Sidebar com filtro por **sessão de corrida** (tipo `Race`, por ano)
- ✅ Painel principal com **métricas da sessão**: País, Circuito, Data
- ✅ Seleção de **múltiplos pilotos** via `st.multiselect` (carregados da coleção `drivers`)
- ✅ Gráfico interativo de **tempo por volta** (`lap_duration` × `lap_number`) com Plotly
- ✅ Tabela expansível com **dados brutos** das voltas (setores, pit out lap, etc.)
- ✅ Cache com `@st.cache_data` em todas as queries (evita reconsultar o banco a cada interação)

---

## TODO – O que falta implementar (~50% restante)

A seguir estão as tarefas que precisam ser concluídas, em ordem de prioridade:

### 1. Análise estatística por piloto (ALTA PRIORIDADE)
**Arquivo:** `streamlit_app.py` (nova seção após o gráfico)  
**O que fazer:**
- Calcular e exibir para cada piloto selecionado:
  - Melhor volta (`lap_duration.min()`)
  - Volta média (`lap_duration.mean()`)
  - Desvio padrão (`lap_duration.std()`)
- Exibir num `st.dataframe` comparativo ou em colunas com `st.metric`

```python
# Exemplo de como calcular no DataFrame já existente (df)
stats = df.groupby("piloto")["lap_duration"].agg(
    melhor_volta="min",
    media="mean",
    desvio_padrao="std"
).reset_index()
st.dataframe(stats, use_container_width=True, hide_index=True)
```

---

### 2. Gráfico de setores (ALTA PRIORIDADE)
**Arquivo:** `streamlit_app.py` (nova aba ou seção)  
**O que fazer:**
- Adicionar um segundo gráfico mostrando `duration_sector_1`, `duration_sector_2`, `duration_sector_3` para os pilotos selecionados
- Pode usar `px.bar` com `barmode="group"` agrupado por volta, ou um segundo `px.line`
- O DataFrame `df` já tem as colunas de setor, só precisa fazer o melt e plotar

```python
# Exemplo de como preparar os dados dos setores
df_setores = df[["piloto", "lap_number", "duration_sector_1", "duration_sector_2", "duration_sector_3"]].copy()
df_melt = df_setores.melt(
    id_vars=["piloto", "lap_number"],
    var_name="setor",
    value_name="duracao"
)
fig_setores = px.line(df_melt, x="lap_number", y="duracao", color="piloto",
                      facet_col="setor", template="plotly_dark")
st.plotly_chart(fig_setores, use_container_width=True)
```

---

### 3. Identificar e destacar pit stops no gráfico principal (MÉDIA PRIORIDADE)
**Arquivo:** `streamlit_app.py`  
**O que fazer:**
- Usar a coluna `is_pit_out_lap` (booleana) que já está no `df` para marcar visualmente as voltas de saída do pit no gráfico principal
- Adicionar uma camada de scatter por cima do line chart, filtrando `df[df["is_pit_out_lap"] == True]`

```python
# Exemplo: adicionar camada de pit stops no fig existente
df_pits = df[df["is_pit_out_lap"] == True]
for piloto in df_pits["piloto"].unique():
    dados_pit = df_pits[df_pits["piloto"] == piloto]
    fig.add_trace(go.Scatter(
        x=dados_pit["lap_number"],
        y=dados_pit["lap_duration"],
        mode="markers",
        marker=dict(symbol="triangle-up", size=12, color="yellow"),
        name=f"Pit Out – {piloto}",
    ))
```

---

### 4. Filtro por tipo de sessão (MÉDIA PRIORIDADE)
**Arquivo:** `db_utils.py` + `streamlit_app.py`  
**O que fazer:**
- A função `get_sessions_by_year` atualmente filtra só `"Race"`. Adicionar opção na sidebar para escolher entre `["Race", "Qualifying", "Practice 1", "Practice 2", "Practice 3"]`
- Passar esse filtro como parâmetro para a função

```python
# Em db_utils.py – alterar a assinatura:
def get_sessions_by_year(year: int, session_type: str = "Race"):
    filtro = {"year": year, "session_type": session_type}
    ...

# Em streamlit_app.py – adicionar na sidebar:
tipo_sessao = st.sidebar.selectbox("Tipo de Sessão", ["Race", "Qualifying", "Practice 1", "Practice 2", "Practice 3"])
sessoes = carregar_sessoes(ano_selecionado, tipo_sessao)
```

---

### 5. Exportar dados como CSV (BAIXA PRIORIDADE)
**Arquivo:** `streamlit_app.py`  
**O que fazer:**
- Após a tabela de dados brutos, adicionar um botão de download com `st.download_button`

```python
csv = df[colunas_exibir].to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Baixar dados como CSV",
    data=csv,
    file_name=f"voltas_{session_key}.csv",
    mime="text/csv",
)
```

---

### 6. Ajuste visual e polish final (BAIXA PRIORIDADE)
- Melhorar o CSS inline no `st.markdown` para deixar as métricas com fundo colorido
- Adicionar ícone/cor da equipa em cada piloto (campo `team_colour` se disponível na coleção `drivers`)
- Testar com dados reais do GP da Itália 2023 (`session_key=9159`) conforme descrito no documento da prática

---

## Notas importantes

- **NÃO** modifique a lógica de `get_client()` / `get_db()` em `db_utils.py` sem necessidade — o singleton de conexão funciona bem pra Streamlit
- O cache `@st.cache_data(ttl=300)` nas funções de query é intencional. Se precisar forçar refresh, pode reduzir o TTL ou usar `st.cache_data.clear()`  
- A coleção `drivers` pode não ter `name_acronym` em todas as versões da API — o código já tem fallback com `str(driver_number)`
- Testar localmente com `streamlit run streamlit_app.py` após criar o `.env` a partir do `.env.example`

---

**Qualquer dúvida, ver o documento original:** `Prática 04 - Manipulação dos Dados em Banco MongoDB Consultas MongoDB.md`
