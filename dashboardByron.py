import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PALETA DE CORES DA MARCA
# =========================================================
COR_AZUL = "#2D9FE0"
COR_LARANJA = "#D46A2E"
COR_VERDE = "#28DCBD"
PALETA = [COR_AZUL, COR_LARANJA, COR_VERDE]

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Byron Data Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# MODO DE TESTE (AUTENTICAÇÃO DESATIVADA TEMPORARIAMENTE)
# =========================================================
with st.sidebar:
    st.info(":material/developer_mode: **Modo de Teste Local**\nAutenticação desativada para validação do painel.")
    st.markdown("---")

# =========================================================
# LINKS DOS CSVs (SUBSTITUA PELAS SUAS URLs PÚBLICAS DO GOOGLE SHEETS)
# =========================================================
LINK_COMERCIAL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3_WYtPMw6Ll4S38ApBIC04x4cTzp2SPHyBzvR5Evk_gSkd1rN2oYxP86JLcdOd1cH7-B2OfOcByjz/pub?gid=1889107330&single=true&output=csv" 
LINK_ACADEMICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3_WYtPMw6Ll4S38ApBIC04x4cTzp2SPHyBzvR5Evk_gSkd1rN2oYxP86JLcdOd1cH7-B2OfOcByjz/pub?gid=544047503&single=true&output=csv"

# =========================================================
# FUNÇÃO DE CARGA, LIMPEZA E ENGENHARIA DE DADOS
# =========================================================
@st.cache_data
def carregar_dados(url):
    df = pd.read_csv(url)

    # 1. Tratamento de taxas vindas como string com vírgula decimal
    colunas_taxa = [
        "Taxa de engajamento",
        "Taxa de Conversão de Perfil (%)",
        "Taxa de Atração",
        "Fator de Retenção e Viralidade"
    ]

    for col in colunas_taxa:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .astype(float)
                * 100
            )

    # 2. Tratamento de colunas numéricas de engajamento
    colunas_interacao = [
        "Curtidas", "Comentários", "Reposts",
        "Compartilhamentos", "Salvamentos"
    ]
    for col in colunas_interacao:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 3. Interações Totais calculadas via código
    df["Interações Totais"] = df[colunas_interacao].sum(axis=1)

    # 4. Cálculo explícito de métricas derivadas em Python
    views_safe = df["Visualizações"].replace(0, 1)
    visitas_safe = df["Visitas ao perfil"].replace(0, 1)

    df["Taxa_Engajamento_Calc"] = (df["Interações Totais"] / views_safe) * 100
    df["Taxa_Conversao_Perfil_Calc"] = (df["Seguidores novos"] / visitas_safe) * 100
    df["Taxa_Amplificacao_Calc"] = ((df["Compartilhamentos"] + df["Reposts"]) / views_safe) * 100
    df["Taxa_Salvamento_Calc"] = (df["Salvamentos"] / views_safe) * 100

    # 5. Detecção e conversão de coluna temporal (Data)
    colunas_data_possiveis = ["Data", "Data de Publicação", "Data de publicação", "data"]
    col_data_encontrada = None
    for c in colunas_data_possiveis:
        if c in df.columns:
            col_data_encontrada = c
            break

    if col_data_encontrada:
        df["Data_Parsed"] = pd.to_datetime(df[col_data_encontrada], dayfirst=True, errors="coerce")
        df = df.sort_values("Data_Parsed")
    else:
        df["Data_Parsed"] = None

    return df, col_data_encontrada


def remover_outliers_iqr(df, coluna):
    """Remove outliers de uma coluna numérica usando a regra do IQR (1.5x)."""
    q1 = df[coluna].quantile(0.25)
    q3 = df[coluna].quantile(0.75)
    iqr = q3 - q1
    limite_superior = q3 + 1.5 * iqr
    limite_inferior = q1 - 1.5 * iqr
    return df[(df[coluna] >= limite_inferior) & (df[coluna] <= limite_superior)]


# =========================================================
# SIDEBAR / CONTROLES
# =========================================================
st.sidebar.title(":material/tune: Configurações")

modo = st.sidebar.radio(
    "Qual contexto você quer analisar agora?",
    ["Acadêmico (Comunidade UNIFEI)", "Comercial (Prospecção B2B)"]
)

filtrar_outliers = st.sidebar.checkbox(
    ":material/shield: Filtrar outliers (eventos atípicos)",
    value=False,
    help="Remove posts com pico de Visualizações fora do padrão estatístico (regra do IQR)."
)

if st.sidebar.button(":material/refresh: Atualizar dados agora"):
    st.cache_data.clear()
    st.sidebar.success("Cache limpo! Dados recarregados.")

st.sidebar.markdown("---")

# Define URL e títulos
if modo.startswith("Comercial"):
    url_dados = LINK_COMERCIAL
    titulo_principal = ":material/query_stats: Byron Data Engine — Funil Comercial"
    subtitulo = "Desempenho de conteúdo orgânico na geração de leads e prospecção B2B."
else:
    url_dados = LINK_ACADEMICO
    titulo_principal = ":material/school: Byron Data Engine — Funil Acadêmico (UNIFEI)"
    subtitulo = "Engajamento e atração da comunidade acadêmica da UNIFEI."

# =========================================================
# CARREGAMENTO E FILTRAGEM DOS DADOS
# =========================================================
df_bruto, col_data = carregar_dados(url_dados)

# Filtro por Formato de Post na Sidebar
formatos_disponiveis = df_bruto["Tipo do post"].dropna().unique().tolist()
formatos_selecionados = st.sidebar.multiselect(
    "Filtrar por Formato de Post:",
    options=formatos_disponiveis,
    default=formatos_disponiveis
)

df_filtrado = df_bruto[df_bruto["Tipo do post"].isin(formatos_selecionados)]

if filtrar_outliers:
    df = remover_outliers_iqr(df_filtrado, "Visualizações")
    qtd_removidos = len(df_filtrado) - len(df)
else:
    df = df_filtrado.copy()
    qtd_removidos = 0

# =========================================================
# SIMULADOR DE METAS (BARRA LATERAL)
# =========================================================
st.sidebar.markdown("---")
st.sidebar.subheader(":material/calculate: Simulador de Metas")
meta_seguidores = st.sidebar.number_input("Meta de Novos Seguidores:", min_value=1, value=20, step=5)

tx_conv_media = df["Taxa de Conversão de Perfil (%)"].mean()
if pd.notnull(tx_conv_media) and tx_conv_media > 0:
    visitas_necessarias = (meta_seguidores / (tx_conv_media / 100))
    st.sidebar.info(
        f"Para alcançar **{meta_seguidores}** novos seguidores com a taxa de conversão média atual "
        f"({tx_conv_media:.2f}%), o perfil precisa receber aproximadamente **{visitas_necessarias:,.0f}** visitas."
    )

st.sidebar.markdown("---")
st.sidebar.caption("Byron Data Engine • Painel de Testes")

# =========================================================
# CABEÇALHO DA PÁGINA
# =========================================================
st.title(titulo_principal)
st.markdown(f"##### {subtitulo}")

if not col_data:
    st.warning(
        ":material/info: **Coluna de data não encontrada na planilha.** "
        "Para ativar a evolução temporal por datas exatas, adicione uma coluna chamada **'Data'** no Google Sheets. "
        "Enquanto isso, a linha do tempo usará a sequência dos posts."
    )

if filtrar_outliers:
    st.info(
        f":material/shield: Filtro de outliers ativo — {qtd_removidos} post(s) atípico(s) "
        f"removidos (regra do IQR sobre 'Visualizações')."
    )

st.markdown("---")

# =========================================================
# TOP SCORECARDS (MÉTRICAS PRINCIPAIS)
# =========================================================
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric(
        label=":material/visibility: Visualizações Totais",
        value=f"{df['Visualizações'].sum():,.0f}".replace(",", ".")
    )

with c2:
    st.metric(
        label=":material/bolt: Engajamento Médio",
        value=f"{df['Taxa de engajamento'].mean():.2f}%"
    )

with c3:
    st.metric(
        label=":material/sync_alt: Conversão de Perfil",
        value=f"{df['Taxa de Conversão de Perfil (%)'].mean():.2f}%"
    )

with c4:
    st.metric(
        label=":material/share: Taxa de Viralidade",
        value=f"{df['Taxa_Amplificacao_Calc'].mean():.2f}%"
    )

with c5:
    st.metric(
        label=":material/person_add: Novos Seguidores",
        value=f"{df['Seguidores novos'].sum():,.0f}".replace(",", ".")
    )

st.markdown("---")

# =========================================================
# TIMELINE / GRÁFICO TEMPORAL DE EVOLUÇÃO
# =========================================================
st.subheader(":material/timeline: Timeline Temporal de Performance")
st.caption("Acompanhe a evolução do engajamento e métricas interativas ao longo das publicações.")

metrica_timeline = st.multiselect(
    "Selecione as métricas para visualizar na linha do tempo:",
    options=["Visualizações", "Curtidas", "Comentários", "Interações Totais", "Seguidores novos"],
    default=["Curtidas", "Comentários", "Interações Totais"],
    key="select_timeline_metrics"
)

fig_timeline = go.Figure()
eixo_x = df["Data_Parsed"] if col_data and df["Data_Parsed"].notnull().any() else df["Post"]

if metrica_timeline:
    for idx, metrica in enumerate(metrica_timeline):
        fig_timeline.add_trace(go.Scatter(
            x=eixo_x,
            y=df[metrica],
            mode="lines+markers",
            name=metrica,
            line=dict(color=PALETA[idx % len(PALETA)], width=3),
            marker=dict(size=7)
        ))

    fig_timeline.update_layout(
        height=450,
        margin=dict(t=30, b=30),
        xaxis_title="Data de Publicação" if col_data else "Post / Publicação",
        yaxis_title="Quantidade",
        hovermode="x unified"
    )

    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.info("Selecione ao menos uma métrica acima para gerar o gráfico da timeline.")

st.markdown("---")

# =========================================================
# LEADERBOARD DINÂMICO
# =========================================================
st.subheader(":material/trophy: Destaques do Período")

if not df.empty:
    top_engajamento = df.loc[df["Taxa de engajamento"].idxmax()]
    top_conversao = df.loc[df["Taxa de Conversão de Perfil (%)"].idxmax()]
    top_retencao = df.loc[df["Fator de Retenção e Viralidade"].idxmax()]

    lb1, lb2, lb3 = st.columns(3)

    with lb1:
        st.markdown(
            f"""
            <div style="background-color:#1E293B; padding:20px; border-radius:12px; text-align:center; border:1px solid {COR_AZUL};">
                <p style="font-size:14px; color:#A5B4FC; margin-bottom:4px;">MAIOR ENGAJAMENTO</p>
                <p style="font-size:18px; color:white; font-weight:bold; margin-bottom:2px;">{top_engajamento['Post']}</p>
                <p style="font-size:26px; color:{COR_AZUL}; font-weight:bold; margin-top:6px;">{top_engajamento['Taxa de engajamento']:.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with lb2:
        st.markdown(
            f"""
            <div style="background-color:#1E293B; padding:20px; border-radius:12px; text-align:center; border:1px solid {COR_LARANJA};">
                <p style="font-size:14px; color:#A5B4FC; margin-bottom:4px;">MAIOR CONVERSÃO DE PERFIL</p>
                <p style="font-size:18px; color:white; font-weight:bold; margin-bottom:2px;">{top_conversao['Post']}</p>
                <p style="font-size:26px; color:{COR_LARANJA}; font-weight:bold; margin-top:6px;">{top_conversao['Taxa de Conversão de Perfil (%)']:.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with lb3:
        st.markdown(
            f"""
            <div style="background-color:#1E293B; padding:20px; border-radius:12px; text-align:center; border:1px solid {COR_VERDE};">
                <p style="font-size:14px; color:#A5B4FC; margin-bottom:4px;">MAIOR VIRALIDADE / RETENÇÃO</p>
                <p style="font-size:18px; color:white; font-weight:bold; margin-bottom:2px;">{top_retencao['Post']}</p>
                <p style="font-size:26px; color:{COR_VERDE}; font-weight:bold; margin-top:6px;">{top_retencao['Fator de Retenção e Viralidade']:.2f}%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("---")

# =========================================================
# FUNIL DE CONVERSÃO & MATRIZ ESTRATÉGICA
# =========================================================
col_funil, col_scatter = st.columns(2)

with col_funil:
    st.subheader(":material/filter_alt: Funil de Conversão")
    funil_valores = [
        df["Visualizações"].sum(),
        df["Visitas ao perfil"].sum(),
        df["Seguidores novos"].sum()
    ]
    funil_labels = ["Visualizações", "Visitas ao Perfil", "Seguidores Novos"]

    fig_funil = go.Figure(go.Funnel(
        y=funil_labels,
        x=funil_valores,
        textinfo="value+percent initial",
        marker={"color": PALETA}
    ))
    fig_funil.update_layout(height=420, margin=dict(t=20, b=20))
    st.plotly_chart(fig_funil, use_container_width=True)

with col_scatter:
    st.subheader(":material/my_location: Matriz Alcance x Engajamento")
    fig_scatter = px.scatter(
        df,
        x="Visualizações",
        y="Taxa de engajamento",
        color="Tipo do post",
        size="Interações Totais",
        hover_name="Post",
        size_max=40,
        color_discrete_sequence=PALETA
    )
    fig_scatter.update_layout(height=420, margin=dict(t=20, b=20))
    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# =========================================================
# RADAR POR FORMATO & BOXPLOT ESTATÍSTICO
# =========================================================
col_radar, col_box = st.columns(2)

with col_radar:
    st.subheader(":material/radar: Performance Média por Formato")
    eixos_radar = [
        "Taxa de Atração",
        "Taxa de engajamento",
        "Fator de Retenção e Viralidade",
        "Taxa de Conversão de Perfil (%)"
    ]
    formatos_presentes = df["Tipo do post"].dropna().unique()

    fig_radar = go.Figure()
    for i, formato in enumerate(formatos_presentes):
        df_formato = df[df["Tipo do post"] == formato]
        medias = [df_formato[eixo].mean() for eixo in eixos_radar]

        fig_radar.add_trace(go.Scatterpolar(
            r=medias + [medias[0]],
            theta=eixos_radar + [eixos_radar[0]],
            fill='toself',
            name=formato,
            line_color=PALETA[i % len(PALETA)],
            opacity=0.6
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True)),
        height=450,
        margin=dict(t=30, b=30),
        legend=dict(orientation="h", y=-0.1)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_box:
    st.subheader(":material/analytics: Distribuição de Engajamento por Formato")
    fig_box = px.box(
        df,
        x="Tipo do post",
        y="Taxa de engajamento",
        color="Tipo do post",
        points="all",
        color_discrete_sequence=PALETA
    )
    fig_box.update_layout(height=450, margin=dict(t=30, b=30), showlegend=False)
    st.plotly_chart(fig_box, use_container_width=True)

st.markdown("---")
st.caption("Byron Data Engine © Modulo de Teste.")