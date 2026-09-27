"""
streamlit_app.py
Interface principal do OpenF1 Data Explorer.
Conecta com o MongoDB via db_utils e exibe os dados de corrida.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import db_utils

# ---- Configuração da página ----
st.set_page_config(
    page_title="OpenF1 Data Explorer",
    page_icon="🏎️",
    layout="wide",
)

# ---- Estilo extra (pequeno ajuste de cor no header) ----
st.markdown("""
    <style>
        .metric-label { font-size: 0.85rem; }
        .stMetric { background: #1e1e1e; border-radius: 8px; padding: 10px; }
    </style>
""", unsafe_allow_html=True)


# ---- Verifica conexão com o banco ----
@st.cache_resource
def verificar_conexao():
    return db_utils.test_connection()


if not verificar_conexao():
    st.error(
        "❌ Não foi possível conectar ao MongoDB. "
        "Verifique se o servidor está rodando e se o arquivo .env está configurado."
    )
    st.stop()


# ===================== SIDEBAR =====================
st.sidebar.title("🏎️ OpenF1 Data Explorer")
st.sidebar.markdown("---")
st.sidebar.subheader("🔎 Filtros")

# Carrega os anos disponíveis
@st.cache_data(ttl=300)
def carregar_anos():
    return db_utils.get_available_years()

anos = carregar_anos()

if not anos:
    st.sidebar.warning("Nenhum dado encontrado na coleção 'sessions'.")
    st.stop()

ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos)

# Carrega as sessões do ano escolhido
@st.cache_data(ttl=300)
def carregar_sessoes(year):
    return db_utils.get_sessions_by_year(year)

sessoes = carregar_sessoes(ano_selecionado)

if not sessoes:
    st.sidebar.info(f"Sem corridas registradas para {ano_selecionado}.")
    st.stop()

# Monta um dict {nome_exibição: session_key} pra usar no selectbox
opcoes_sessao = {
    f"{s.get('session_name', '?')} – {s.get('country_name', '?')}": s["session_key"]
    for s in sessoes
}

sessao_escolhida_label = st.sidebar.selectbox("Selecione a Corrida", list(opcoes_sessao.keys()))
session_key = opcoes_sessao[sessao_escolhida_label]

st.sidebar.markdown("---")
st.sidebar.caption("Dados via OpenF1 API | MongoDB")


# ===================== PAINEL PRINCIPAL =====================
detalhes = db_utils.get_session_details(session_key)

st.title("🏁 Análise de Corrida")

if detalhes:
    col1, col2, col3 = st.columns(3)
    col1.metric("🌍 País", detalhes.get("country_name", "N/A"))
    col2.metric("🏟️ Circuito", detalhes.get("circuit_short_name", "N/A"))
    data_bruta = detalhes.get("date_start", "N/A")
    # data pode vir como string ou datetime
    data_fmt = str(data_bruta)[:10] if data_bruta != "N/A" else "N/A"
    col3.metric("📅 Data", data_fmt)
else:
    st.warning("Não foi possível carregar os detalhes desta sessão.")

st.markdown("---")


# ===================== SELEÇÃO DE PILOTOS =====================
st.subheader("👤 Seleção de Pilotos")

@st.cache_data(ttl=300)
def carregar_pilotos(sk):
    return db_utils.get_drivers_in_session(sk)

pilotos = carregar_pilotos(session_key)

if not pilotos:
    st.info("Nenhum piloto encontrado para esta sessão na coleção 'drivers'.")
    st.stop()

# Monta mapa {nome_exibição: driver_number}
opcoes_pilotos = {
    f"{p.get('name_acronym', '?')} – {p.get('full_name', '?')} ({p.get('team_name', '?')})": p["driver_number"]
    for p in pilotos
}

pilotos_selecionados_labels = st.multiselect(
    "Escolha os pilotos para comparar:",
    list(opcoes_pilotos.keys()),
    default=list(opcoes_pilotos.keys())[:2] if len(opcoes_pilotos) >= 2 else list(opcoes_pilotos.keys()),
)

if not pilotos_selecionados_labels:
    st.warning("Selecione pelo menos um piloto para ver o gráfico.")
    st.stop()

driver_numbers = [opcoes_pilotos[lbl] for lbl in pilotos_selecionados_labels]

# Mapa inverso: driver_number -> sigla, pra usar nas legendas do gráfico
num_para_sigla = {
    p["driver_number"]: p.get("name_acronym", str(p["driver_number"]))
    for p in pilotos
}


# ===================== GRÁFICO DE DESEMPENHO =====================
st.subheader("📈 Tempo por Volta (lap_duration)")

@st.cache_data(ttl=300)
def carregar_voltas(sk, drivers):
    return db_utils.get_laps_for_drivers(sk, drivers)

voltas_raw = carregar_voltas(session_key, driver_numbers)

if not voltas_raw:
    st.info("Sem dados de voltas para os pilotos selecionados nesta sessão.")
else:
    df = pd.DataFrame(voltas_raw)

    # adiciona coluna com o nome/sigla do piloto pra legenda
    df["piloto"] = df["driver_number"].map(num_para_sigla)

    fig = px.line(
        df,
        x="lap_number",
        y="lap_duration",
        color="piloto",
        markers=True,
        title=f"Tempo de Volta – {sessao_escolhida_label}",
        labels={
            "lap_number": "Nº da Volta",
            "lap_duration": "Duração (s)",
            "piloto": "Piloto",
        },
        template="plotly_dark",
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=5))
    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---- Tabela de dados brutos ----
    with st.expander("📋 Ver tabela de dados"):
        colunas_exibir = [c for c in [
            "piloto", "lap_number", "lap_duration",
            "duration_sector_1", "duration_sector_2", "duration_sector_3",
            "is_pit_out_lap"
        ] if c in df.columns]
        st.dataframe(
            df[colunas_exibir].sort_values(["piloto", "lap_number"]),
            use_container_width=True,
            hide_index=True,
        )
