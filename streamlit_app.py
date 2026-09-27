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
        .stMetric { background: #172329; border-left: 3px solid #00d2be; border-radius: 6px; padding: 10px 14px; }
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

tipos_sessao = ["Race", "Qualifying", "Practice 1", "Practice 2", "Practice 3"]
tipo_sessao = st.sidebar.selectbox("Tipo de Sessão", tipos_sessao)

# Carrega as sessões do ano e tipo escolhidos
@st.cache_data(ttl=300)
def carregar_sessoes(year, session_type):
    return db_utils.get_sessions_by_year(year, session_type)

sessoes = carregar_sessoes(ano_selecionado, tipo_sessao)

if not sessoes:
    st.sidebar.info(f"Sem sessões do tipo {tipo_sessao} registradas para {ano_selecionado}.")
    st.stop()

# Monta um dict {nome_exibição: session_key} pra usar no selectbox
opcoes_sessao = {
    f"{s.get('session_name', tipo_sessao)} – {s.get('country_name', '?')} ({str(s.get('date_start', ''))[:10]})": s["session_key"]
    for s in sessoes
}

sessao_escolhida_label = st.sidebar.selectbox("Selecione a Sessão", list(opcoes_sessao.keys()))
session_key = opcoes_sessao[sessao_escolhida_label]

st.sidebar.markdown("---")
st.sidebar.caption("Dados via OpenF1 API | MongoDB")


# ===================== PAINEL PRINCIPAL =====================
@st.cache_data(ttl=300)
def carregar_detalhes_sessao(sk):
    return db_utils.get_session_details(sk)


detalhes = carregar_detalhes_sessao(session_key)

st.title("🏁 OpenF1 Data Explorer")

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
    f"{p.get('name_acronym') or p['driver_number']} – {p.get('full_name', '?')} ({p.get('team_name', '?')})": p["driver_number"]
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
    p["driver_number"]: p.get("name_acronym") or str(p["driver_number"])
    for p in pilotos
}

cores_pilotos = {}
for piloto in pilotos:
    sigla = piloto.get("name_acronym") or str(piloto["driver_number"])
    cor = piloto.get("team_colour")
    if isinstance(cor, str):
        cor = cor.strip()
        if len(cor) == 6 and not cor.startswith("#"):
            cor = f"#{cor}"
        if len(cor) == 7 and cor.startswith("#") and all(
            caractere in "0123456789abcdefABCDEF" for caractere in cor[1:]
        ):
            cores_pilotos[sigla] = cor


# ===================== GRÁFICO DE DESEMPENHO =====================
st.subheader("📈 Tempo por Volta (lap_duration)")

@st.cache_data(ttl=300)
def carregar_voltas(sk, drivers):
    # driver_numbers precisa ser tuple porque lista não é hashable no cache
    return db_utils.get_laps_for_drivers(sk, list(drivers))

voltas_raw = carregar_voltas(session_key, tuple(driver_numbers))

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
        color_discrete_map=cores_pilotos,
    )
    fig.update_traces(line=dict(width=2), marker=dict(size=5))

    if "is_pit_out_lap" in df.columns:
        df_pits = df[df["is_pit_out_lap"].eq(True)]
        for piloto in df_pits["piloto"].unique():
            dados_pit = df_pits[df_pits["piloto"] == piloto]
            fig.add_trace(go.Scatter(
                x=dados_pit["lap_number"],
                y=dados_pit["lap_duration"],
                mode="markers",
                marker=dict(symbol="triangle-up", size=11, color="#f4d35e"),
                name=f"Saída dos boxes – {piloto}",
                hovertemplate="Volta %{x}<br>%{y:.3f} s<extra>Saída dos boxes</extra>",
            ))

    fig.update_layout(
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---- Estatísticas por piloto ----
    st.subheader("📊 Estatísticas por Piloto")
    estatisticas = (
        df.groupby("piloto")["lap_duration"]
        .agg(melhor_volta="min", media="mean", desvio_padrao="std")
        .reset_index()
        .rename(columns={
            "piloto": "Piloto",
            "melhor_volta": "Melhor volta (s)",
            "media": "Média (s)",
            "desvio_padrao": "Desvio padrão (s)",
        })
        .round(3)
    )
    st.dataframe(estatisticas, use_container_width=True, hide_index=True)

    # ---- Comparação de setores ----
    colunas_setores = [
        coluna for coluna in [
            "duration_sector_1", "duration_sector_2", "duration_sector_3"
        ] if coluna in df.columns
    ]
    if colunas_setores:
        df_setores = df[["piloto", "lap_number", *colunas_setores]].melt(
            id_vars=["piloto", "lap_number"],
            var_name="setor",
            value_name="duracao",
        )
        df_setores["duracao"] = pd.to_numeric(df_setores["duracao"], errors="coerce")
        df_setores = df_setores.dropna(subset=["duracao"])
        if not df_setores.empty:
            nomes_setores = {
                "duration_sector_1": "Setor 1",
                "duration_sector_2": "Setor 2",
                "duration_sector_3": "Setor 3",
            }
            df_setores["setor"] = df_setores["setor"].map(nomes_setores)
            st.subheader("⏱️ Tempos por Setor")
            fig_setores = px.line(
                df_setores,
                x="lap_number",
                y="duracao",
                color="piloto",
                facet_col="setor",
                markers=True,
                labels={
                    "lap_number": "Nº da Volta",
                    "duracao": "Duração (s)",
                    "piloto": "Piloto",
                    "setor": "Setor",
                },
                template="plotly_dark",
                color_discrete_map=cores_pilotos,
            )
            fig_setores.update_layout(height=420, hovermode="x unified")
            st.plotly_chart(fig_setores, use_container_width=True)
        else:
            st.info("Não há tempos de setor registrados para estas voltas.")

    # ---- Tabela de dados brutos ----
    # colunas_exibir definida antes do expander pra poder ser usada no download_button
    colunas_exibir = [c for c in [
        "piloto", "lap_number", "lap_duration",
        "duration_sector_1", "duration_sector_2", "duration_sector_3",
        "is_pit_out_lap"
    ] if c in df.columns]

    with st.expander("📋 Ver tabela de dados"):
        st.dataframe(
            df[colunas_exibir].sort_values(["piloto", "lap_number"]),
            use_container_width=True,
            hide_index=True,
        )

    st.download_button(
        label="⬇️ Baixar dados como CSV",
        data=df[colunas_exibir].sort_values(["piloto", "lap_number"]).to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name=f"voltas_{session_key}.csv",
        mime="text/csv",
    )
