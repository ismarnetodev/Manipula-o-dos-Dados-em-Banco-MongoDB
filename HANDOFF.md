# HANDOFF.md – OpenF1 Data Explorer

**Branch:** `branch-ismar`  
**Data:** 27/09/2026  
**Responsável até aqui:** Rejan  

---

## Estado atual do repositório

### O que está implementado

| Arquivo | O que faz |
|---|---|
| `requirements.txt` | Todas as dependências definidas (streamlit, pymongo, plotly, pandas, python-dotenv) |
| `.env.example` | Modelo do arquivo de configuração com `MONGODB_URI` e `DB_NAME` |
| `.gitignore` | Ignora `.env`, `__pycache__`, `.venv` |
| `db_utils.py` | Módulo completo de conexão e consultas ao MongoDB |
| `streamlit_app.py` | Interface com filtros, métricas, comparação de voltas e setores, estatísticas, tabela e exportação |
| `README.md` | Instruções de instalação, execução no PowerShell e funcionalidades |

### Funcionalidades implementadas

- ✅ Conexão ao MongoDB via variável de ambiente (`.env`)
- ✅ Teste de conexão na inicialização da app (com `st.stop()` se falhar)
- ✅ Sidebar com filtro por **ano** (carregado dinamicamente da coleção `sessions`)
- ✅ Sidebar com filtro por **tipo de sessão** (`Race`, `Qualifying` e práticas) e sessão, por ano
- ✅ Painel principal com **métricas da sessão**: País, Circuito, Data
- ✅ Seleção de **múltiplos pilotos** via `st.multiselect` (carregados da coleção `drivers`)
- ✅ Gráfico interativo de **tempo por volta** (`lap_duration` × `lap_number`) com Plotly
- ✅ Estatísticas por piloto: melhor volta, média e desvio padrão
- ✅ Gráfico comparativo dos três setores
- ✅ Marcadores para voltas de saída dos boxes e cores de equipe quando disponíveis
- ✅ Tabela expansível com **dados brutos** das voltas (setores, pit out lap, etc.)
- ✅ Download dos dados filtrados em CSV compatível com Excel
- ✅ Cache com `@st.cache_data` em todas as queries (evita reconsultar o banco a cada interação)

---

## Entregas concluídas nesta etapa

As seis tarefas listadas abaixo foram incorporadas. Os trechos de código permanecem como referência do handoff original.

### ✅ 1. Análise estatística por piloto (ALTA PRIORIDADE)
**Arquivo:** `streamlit_app.py` (nova seção após o gráfico)  
**Implementado:**
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

### ✅ 2. Gráfico de setores (ALTA PRIORIDADE)
**Arquivo:** `streamlit_app.py` (nova aba ou seção)  
**Implementado:**
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

### ✅ 3. Identificar e destacar pit stops no gráfico principal (MÉDIA PRIORIDADE)
**Arquivo:** `streamlit_app.py`  
**Implementado:**
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

### ✅ 4. Filtro por tipo de sessão (MÉDIA PRIORIDADE)
**Arquivo:** `db_utils.py` + `streamlit_app.py`  
**Implementado:**
- `get_sessions_by_year` recebe o tipo escolhido na sidebar e filtra entre `Race`, `Qualifying` e `Practice 1`, `Practice 2` ou `Practice 3`.

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

### ✅ 5. Exportar dados como CSV (BAIXA PRIORIDADE)
**Arquivo:** `streamlit_app.py`  
**Implementado:**
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
- ✅ O CSS das métricas foi atualizado.
- ✅ As cores de equipe são usadas nos gráficos quando o campo `team_colour` está disponível.
- ⏳ Ainda falta validar com dados reais do GP da Itália 2023 (`session_key=9159`); isso requer MongoDB acessível e populado.

---

## Notas importantes

- **NÃO** modifique a lógica de `get_client()` / `get_db()` em `db_utils.py` sem necessidade — o singleton de conexão funciona bem pra Streamlit
- O cache `@st.cache_data(ttl=300)` nas funções de query é intencional. Se precisar forçar refresh, pode reduzir o TTL ou usar `st.cache_data.clear()`  
- A coleção `drivers` pode não ter `name_acronym` em todas as versões da API — o código já tem fallback com `str(driver_number)`
- Executar no Windows sem ativar o ambiente: `.\venv\Scripts\python.exe -m streamlit run streamlit_app.py` após configurar `.env`.

---

**Qualquer dúvida, ver o documento original:** `Prática 04 - Manipulação dos Dados em Banco MongoDB Consultas MongoDB.md`
