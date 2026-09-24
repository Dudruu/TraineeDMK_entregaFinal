import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =========================================================
# PALETA DE CORES DA MARCA (RIGOROSAMENTE MANTIDA)
# =========================================================
COR_AZUL = "#2D9FE0"
COR_LARANJA = "#D46A2E"
COR_VERDE = "#28DCBD"
COR_FUNDO_CARD = "#1E293B"
COR_TEXTO_MUTED = "#94A3B8"
COR_GRID = "#334155"
PALETA = [COR_AZUL, COR_LARANJA, COR_VERDE]

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Byron Data Engine",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# ESTILIZAÇÃO CSS (cartões de KPI primários/secundários, abas, espaçamento)
# =========================================================
st.markdown(f"""
    <style>
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2.5rem;
    }}

    /* --- KPIs primários (destaque no topo) --- */
    .kpi-card {{
        background-color: {COR_FUNDO_CARD};
        border-radius: 10px;
        padding: 18px 20px;
        border-left: 4px solid {COR_AZUL};
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.15);
        margin-bottom: 4px;
    }}
    .kpi-card-orange {{ border-left-color: {COR_LARANJA}; }}
    .kpi-card-green {{ border-left-color: {COR_VERDE}; }}
    .kpi-title {{
        font-size: 0.82rem;
        font-weight: 600;
        color: {COR_TEXTO_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }}
    .kpi-value {{
        font-size: 1.9rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
        line-height: 1.1;
    }}

    /* --- KPIs secundários (métricas derivadas, hierarquia menor) --- */
    .kpi-card-sec {{
        background-color: {COR_FUNDO_CARD};
        border-radius: 8px;
        padding: 12px 16px;
        border-top: 3px solid {COR_AZUL};
        opacity: 0.94;
        margin-bottom: 4px;
    }}
    .kpi-card-sec.orange {{ border-top-color: {COR_LARANJA}; }}
    .kpi-card-sec.green {{ border-top-color: {COR_VERDE}; }}
    .kpi-title-sec {{
        font-size: 0.72rem;
        font-weight: 600;
        color: {COR_TEXTO_MUTED};
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 4px;
    }}
    .kpi-value-sec {{
        font-size: 1.25rem;
        font-weight: 700;
        color: #E2E8F0;
        margin: 0;
    }}

    /* --- Cartão de destaque (metas / callouts) --- */
    .meta-card {{
        background-color: {COR_FUNDO_CARD};
        border-radius: 10px;
        padding: 18px 22px;
        border: 1px solid {COR_GRID};
    }}

    .section-caption {{
        color: {COR_TEXTO_MUTED};
        font-size: 0.92rem;
        margin-top: -6px;
        margin-bottom: 10px;
    }}

    /* --- Abas de navegação --- */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 6px;
        border-bottom: 1px solid {COR_GRID};
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 44px;
        white-space: pre-wrap;
        border-radius: 8px 8px 0 0;
        padding: 6px 18px;
        color: {COR_TEXTO_MUTED};
        font-weight: 600;
    }}
    .stTabs [aria-selected="true"] {{
        color: #FFFFFF !important;
        border-bottom: 3px solid {COR_AZUL} !important;
    }}

    hr {{
        margin: 1.6rem 0;
        border-color: {COR_GRID};
    }}
    </style>
""", unsafe_allow_html=True)

# =========================================================
# AUTENTICAÇÃO (Google OIDC) — acesso restrito ao domínio da empresa júnior
# =========================================================
DOMINIO_PERMITIDO = "byronsolutions.com"

if not getattr(st.user, "is_logged_in", False):
    st.title(":material/lock: Byron Data Engine")
    st.write("Esse painel é restrito aos membros da empresa júnior. Faça login com o seu e-mail institucional para continuar.")
    if hasattr(st.user, "is_logged_in"):
        st.button(":material/login: Entrar com Google", on_click=st.login, type="primary")
    else:
        st.warning(
            ":material/build: A autenticação com Google ainda não foi configurada neste deploy "
            "(faltam os `secrets` do `[auth]`). Assim que isso for feito, o login passa a ser exigido aqui."
        )
    st.stop()

email_usuario = (getattr(st.user, "email", None) or "").lower()

if not email_usuario.endswith(f"@{DOMINIO_PERMITIDO.lower()}"):
    st.title(":material/block: Acesso não autorizado")
    st.error(
        f"O e-mail **{email_usuario}** não pertence ao domínio **@{DOMINIO_PERMITIDO}**. "
        "Esse painel é restrito aos membros da empresa júnior."
    )
    st.button(":material/logout: Sair", on_click=st.logout)
    st.stop()

# Usuário autenticado e autorizado — exibe as credenciais na barra lateral
with st.sidebar:
    st.markdown(f":material/account_circle: Logado como **{st.user.email}**")
    st.button(":material/logout: Sair", on_click=st.logout)
    st.divider()

# =========================================================
# LINKS DOS CSVs (GOOGLE SHEETS)
# =========================================================
LINK_COMERCIAL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3_WYtPMw6Ll4S38ApBIC04x4cTzp2SPHyBzvR5Evk_gSkd1rN2oYxP86JLcdOd1cH7-B2OfOcByjz/pub?gid=1889107330&single=true&output=csv"
LINK_ACADEMICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3_WYtPMw6Ll4S38ApBIC04x4cTzp2SPHyBzvR5Evk_gSkd1rN2oYxP86JLcdOd1cH7-B2OfOcByjz/pub?gid=544047503&single=true&output=csv"

# =========================================================
# CARGA, TRATAMENTO E ENGENHARIA DE DADOS
# =========================================================
@st.cache_data
def carregar_e_tratar_dados(url):
    df = pd.read_csv(url)

    # 1. Tratamento das taxas numéricas vindas como string no formato decimal brasileiro
    colunas_taxa_originais = [
        "Taxa de engajamento",
        "Taxa de Conversão de Perfil (%)",
        "Taxa de Atração",
        "Fator de Retenção e Viralidade"
    ]
    for col in colunas_taxa_originais:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .astype(float)
                * 100
            )

    # 2. Garantia de consistência das métricas brutas de engajamento
    colunas_interacao = ["Curtidas", "Comentários", "Reposts", "Compartilhamentos", "Salvamentos"]
    for col in colunas_interacao:
        if col not in df.columns:
            df[col] = 0
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 3. Cálculo de interações totais e métricas derivadas
    df["Interações Totais"] = df[colunas_interacao].sum(axis=1)

    views_safe = df["Visualizações"].replace(0, 1)
    visitas_safe = df["Visitas ao perfil"].replace(0, 1)

    df["Taxa_Engajamento_Calc"] = (df["Interações Totais"] / views_safe) * 100
    df["Taxa_Conversao_Perfil_Calc"] = (df["Seguidores novos"] / visitas_safe) * 100
    df["Taxa_Amplificacao_Calc"] = ((df["Compartilhamentos"] + df["Reposts"]) / views_safe) * 100
    df["Taxa_Salvamento_Calc"] = (df["Salvamentos"] / views_safe) * 100
    df["Taxa_Comentario_Calc"] = (df["Comentários"] / views_safe) * 100

    # 4. Checagem de coluna temporal
    colunas_data_possiveis = ["Data", "Data de Publicação", "Data de publicação", "data"]
    col_data_encontrada = None
    for c in colunas_data_possiveis:
        if c in df.columns:
            col_data_encontrada = c
            break

    if col_data_encontrada:
        df["Data_Parsed"] = pd.to_datetime(df[col_data_encontrada], dayfirst=True, errors="coerce")
    else:
        df["Data_Parsed"] = None

    return df, col_data_encontrada


def remover_outliers_iqr(df, coluna="Visualizações"):
    """Remove outliers usando a regra estatística do Amplitude Interquartil (1.5x IQR)."""
    q1 = df[coluna].quantile(0.25)
    q3 = df[coluna].quantile(0.75)
    iqr = q3 - q1
    limite_superior = q3 + 1.5 * iqr
    limite_inferior = q1 - 1.5 * iqr
    return df[(df[coluna] >= limite_inferior) & (df[coluna] <= limite_superior)]


def marcar_anomalias(df, coluna="Visualizações"):
    """Sinaliza posts fora do intervalo de 1.5x IQR (picos e quedas atípicas)."""
    if df.empty:
        df["Anomalia"] = ""
        return df

    q1 = df[coluna].quantile(0.25)
    q3 = df[coluna].quantile(0.75)
    iqr = q3 - q1
    limite_superior = q3 + 1.5 * iqr
    limite_inferior = q1 - 1.5 * iqr

    df["Anomalia"] = ""
    df.loc[df[coluna] > limite_superior, "Anomalia"] = ":material/trending_up: Pico atípico"
    df.loc[df[coluna] < limite_inferior, "Anomalia"] = ":material/trending_down: Queda atípica"
    return df


def calcular_score_composto(df, peso_eng, peso_conv, peso_viral):
    """
    Ranking ponderado (0-100) usando o percentil de cada post dentro do conjunto filtrado.
    """
    pesos_soma = peso_eng + peso_conv + peso_viral
    if df.empty or pesos_soma == 0:
        df["Post_Score"] = 0.0
        return df

    pct_engajamento = df["Taxa de engajamento"].rank(pct=True)
    pct_conversao = df["Taxa de Conversão de Perfil (%)"].rank(pct=True)
    pct_viralidade = df["Fator de Retenção e Viralidade"].rank(pct=True)

    df["Post_Score"] = (
        (pct_engajamento * peso_eng)
        + (pct_conversao * peso_conv)
        + (pct_viralidade * peso_viral)
    ) / pesos_soma * 100

    return df


def estilo_padrao(fig, altura=460, legenda=True, eixo_x_titulo=None, eixo_y_titulo=None, rotacionar_x=False):
    """Aplica um layout consistente a todas as figuras Plotly do painel."""
    fig.update_layout(
        height=altura,
        margin=dict(t=30, b=40, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#CBD5E1", size=13),
        hoverlabel=dict(bgcolor=COR_FUNDO_CARD, font_size=13),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.03, xanchor="right", x=1
        ) if legenda else dict(),
        showlegend=legenda,
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=COR_GRID, zeroline=False,
        title=dict(text=eixo_x_titulo) if eixo_x_titulo else None,
        tickangle=-35 if rotacionar_x else 0
    )
    fig.update_yaxes(showgrid=True, gridcolor=COR_GRID, zeroline=False,
                      title=dict(text=eixo_y_titulo) if eixo_y_titulo else None)
    return fig


def truncar_texto(texto, limite=22):
    texto = str(texto)
    return texto if len(texto) <= limite else texto[:limite - 1] + "…"


def kpi_primario(col, titulo, valor, classe=""):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card {classe}">
                <div class="kpi-title">{titulo}</div>
                <div class="kpi-value">{valor}</div>
            </div>
            """, unsafe_allow_html=True
        )


def kpi_secundario(col, titulo, valor, classe=""):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card-sec {classe}">
                <div class="kpi-title-sec">{titulo}</div>
                <div class="kpi-value-sec">{valor}</div>
            </div>
            """, unsafe_allow_html=True
        )


# =========================================================
# BARRA LATERAL (CONTROLES E FILTROS)
# =========================================================
st.sidebar.title(":material/tune: Painel de Controle")

modo = st.sidebar.radio(
    "Contexto Analítico:",
    ["Acadêmico (Comunidade UNIFEI)", "Comercial (Prospecção B2B)"],
    help="Alterne entre os funis de atração acadêmica e prospecção comercial."
)

url_dados = LINK_COMERCIAL if modo.startswith("Comercial") else LINK_ACADEMICO
df_bruto, col_data_presente = carregar_e_tratar_dados(url_dados)

st.sidebar.divider()

with st.sidebar.expander(":material/filter_list: Filtros de Conteúdo", expanded=True):
    formatos_disponiveis = df_bruto["Tipo do post"].dropna().unique().tolist()
    formatos_selecionados = st.multiselect(
        "Formatos de Post:",
        options=formatos_disponiveis,
        default=formatos_disponiveis
    )

    filtrar_outliers = st.checkbox(
        ":material/shield: Omitir Outliers (IQR)",
        value=False,
        help="Remove posts com picos atípicos de visualizações do cálculo geral."
    )

    if st.button(":material/refresh: Recarregar Dados", width='stretch'):
        st.cache_data.clear()
        st.success("Cache atualizado!")

df_filtrado = df_bruto[df_bruto["Tipo do post"].isin(formatos_selecionados)].copy()

if filtrar_outliers and not df_filtrado.empty:
    df = remover_outliers_iqr(df_filtrado, "Visualizações")
    qtd_removidos = len(df_filtrado) - len(df)
else:
    df = df_filtrado.copy()
    qtd_removidos = 0

with st.sidebar.expander(":material/star: Pesos do Score Composto", expanded=False):
    st.caption("Ajuste a importância de cada taxa no ranking de posts.")
    peso_engajamento = st.slider("Engajamento", 0.0, 1.0, 0.4, 0.05)
    peso_conversao = st.slider("Conversão de Perfil", 0.0, 1.0, 0.3, 0.05)
    peso_viralidade = st.slider("Retenção / Viralidade", 0.0, 1.0, 0.3, 0.05)

with st.sidebar.expander(":material/calculate: Simulador de Metas", expanded=False):
    meta_novos_seguidores = st.number_input("Meta de Novos Seguidores:", min_value=1, value=20, step=5)
    tx_conversao_media = df["Taxa de Conversão de Perfil (%)"].mean() if not df.empty else 0
    if pd.notnull(tx_conversao_media) and tx_conversao_media > 0:
        visitas_necessarias = meta_novos_seguidores / (tx_conversao_media / 100)
    else:
        visitas_necessarias = None

st.sidebar.divider()
st.sidebar.caption("Byron Data Engine v3.0 • Inteligência Orgânica")

# Cálculos que dependem dos filtros e pesos
df = calcular_score_composto(df, peso_engajamento, peso_conversao, peso_viralidade)
df = marcar_anomalias(df, "Visualizações")

# =========================================================
# CABEÇALHO
# =========================================================
if modo.startswith("Comercial"):
    st.title(":material/query_stats: Byron Data Engine — Funil Comercial B2B")
    st.markdown("*Análise de conversão orgânica e geração de leads*")
else:
    st.title(":material/school: Byron Data Engine — Funil Acadêmico UNIFEI")
    st.markdown("*Análise de alcance e engajamento com a comunidade universitária*")

if filtrar_outliers and qtd_removidos > 0:
    st.info(f":material/shield: Filtro estatístico ativo: **{qtd_removidos} post(s)** atípico(s) removido(s) da análise.")

st.markdown("---")

# =========================================================
# HIERARQUIA DE KPIs — Linha 1: métricas primárias
# =========================================================
st.subheader(":material/space_dashboard: Visão Geral de Performance")

total_views = df["Visualizações"].sum() if not df.empty else 0
media_engajamento = df["Taxa de engajamento"].mean() if not df.empty else 0
total_seguidores = df["Seguidores novos"].sum() if not df.empty else 0

kpi1, kpi2, kpi3 = st.columns(3, gap="medium")
kpi_primario(kpi1, "Visualizações", f"{total_views:,.0f}".replace(",", "."))
kpi_primario(kpi2, "Engajamento Médio", f"{media_engajamento:.2f}%", "kpi-card-orange")
kpi_primario(kpi3, "Novos Seguidores", f"{total_seguidores:,.0f}".replace(",", "."), "kpi-card-green")

st.write("")

# Linha 2: métricas derivadas (hierarquia secundária)
media_conversao = df["Taxa de Conversão de Perfil (%)"].mean() if not df.empty else 0
media_amplificacao = df["Taxa_Amplificacao_Calc"].mean() if not df.empty else 0
media_salvamento = df["Taxa_Salvamento_Calc"].mean() if not df.empty else 0
media_comentario = df["Taxa_Comentario_Calc"].mean() if not df.empty else 0

sec1, sec2, sec3, sec4 = st.columns(4, gap="medium")
kpi_secundario(sec1, "Conversão de Perfil", f"{media_conversao:.2f}%")
kpi_secundario(sec2, "Taxa de Amplificação", f"{media_amplificacao:.2f}%", "orange")
kpi_secundario(sec3, "Taxa de Salvamento", f"{media_salvamento:.2f}%", "green")
kpi_secundario(sec4, "Taxa de Comentário", f"{media_comentario:.2f}%")

st.markdown("---")

# =========================================================
# NAVEGAÇÃO POR ABAS
# =========================================================
aba_visao, aba_performance, aba_funil, aba_dados = st.tabs([
    "📈  Visão Geral",
    "🎯  Performance & Ranking",
    "🔻  Funil de Conversão",
    "📋  Dados"
])

# ---------------------------------------------------------
# ABA 1 — VISÃO GERAL
# ---------------------------------------------------------
with aba_visao:

    posts_anomalos = df[df["Anomalia"] != ""] if not df.empty else pd.DataFrame()
    if not posts_anomalos.empty:
        with st.expander(f":material/warning: {len(posts_anomalos)} post(s) com desempenho atípico detectado(s)", expanded=False):
            for _, linha in posts_anomalos.iterrows():
                cor_tag = COR_VERDE if "Pico" in linha["Anomalia"] else COR_LARANJA
                st.markdown(
                    f"""<span style="color:{cor_tag}; font-weight:600;">{linha['Anomalia']}</span>
                    &nbsp;—&nbsp; <b>{linha['Post']}</b>
                    &nbsp;({linha['Visualizações']:,.0f} visualizações)""".replace(",", "."),
                    unsafe_allow_html=True
                )
        st.write("")

    st.subheader(":material/timeline: Timeline de Visualizações, Curtidas e Comentários")
    st.markdown(
        '<p class="section-caption">Acompanhe a evolução das métricas de alcance e '
        'reação ao longo das publicações (ordem cronológica de postagem).</p>',
        unsafe_allow_html=True
    )

    metricas_disponiveis = ["Visualizações", "Curtidas", "Comentários", "Interações Totais", "Seguidores novos"]
    metricas_selecionadas = st.multiselect(
        "Métricas exibidas no gráfico:",
        options=metricas_disponiveis,
        default=["Visualizações", "Curtidas", "Comentários"],
        key="timeline_metrics"
    )

    if metricas_selecionadas and not df.empty:
        eixo_x = df["Data_Parsed"] if (col_data_presente and df["Data_Parsed"].notnull().any()) else df["Post"].apply(truncar_texto)

        fig_timeline = go.Figure()
        for idx, metrica in enumerate(metricas_selecionadas):
            fig_timeline.add_trace(go.Scatter(
                x=eixo_x,
                y=df[metrica],
                mode="lines+markers",
                name=metrica,
                line=dict(color=PALETA[idx % len(PALETA)], width=3),
                marker=dict(size=7, symbol="circle"),
                hovertemplate="%{y:,.0f}<extra>" + metrica + "</extra>"
            ))
        fig_timeline = estilo_padrao(
            fig_timeline, altura=460,
            eixo_x_titulo="Publicação (ordem cronológica)", eixo_y_titulo="Volume",
            rotacionar_x=not (col_data_presente and df["Data_Parsed"].notnull().any())
        )
        fig_timeline.update_layout(hovermode="x unified")
        st.plotly_chart(fig_timeline, width='stretch')
    else:
        st.info("Selecione pelo menos uma métrica acima para gerar o gráfico da timeline.")

    st.markdown("---")

    st.subheader(":material/trophy: Destaques de Impacto")
    if not df.empty:
        top_engajamento = df.loc[df["Taxa de engajamento"].idxmax()]
        top_conversao = df.loc[df["Taxa de Conversão de Perfil (%)"].idxmax()]
        top_viralidade = df.loc[df["Fator de Retenção e Viralidade"].idxmax()]

        lb1, lb2, lb3 = st.columns(3, gap="medium")
        destaques = [
            (lb1, COR_AZUL, "Maior Engajamento", top_engajamento, "Taxa de engajamento"),
            (lb2, COR_LARANJA, "Maior Conversão de Perfil", top_conversao, "Taxa de Conversão de Perfil (%)"),
            (lb3, COR_VERDE, "Maior Retenção / Viralidade", top_viralidade, "Fator de Retenção e Viralidade"),
        ]
        for col, cor, titulo, linha, campo in destaques:
            with col:
                st.markdown(
                    f"""
                    <div style="background-color:{COR_FUNDO_CARD}; padding:20px; border-radius:12px; text-align:center; border:1px solid {cor}; min-height:150px;">
                        <p style="font-size:13px; color:{cor}; font-weight:700; margin-bottom:8px; text-transform:uppercase;">{titulo}</p>
                        <p style="font-size:17px; color:white; font-weight:bold; margin-bottom:6px;">{truncar_texto(linha['Post'], 34)}</p>
                        <p style="font-size:26px; color:{cor}; font-weight:bold; margin:0;">{linha[campo]:.2f}%</p>
                    </div>
                    """, unsafe_allow_html=True
                )

# ---------------------------------------------------------
# ABA 2 — PERFORMANCE & RANKING
# ---------------------------------------------------------
with aba_performance:

    st.subheader(":material/star: Ranking por Score Composto")
    st.markdown(
        f'<p class="section-caption">Índice ponderado (0-100) combinando Engajamento ({peso_engajamento:.0%}), '
        f'Conversão de Perfil ({peso_conversao:.0%}) e Retenção/Viralidade ({peso_viralidade:.0%}). '
        'Ajuste os pesos na barra lateral.</p>',
        unsafe_allow_html=True
    )
    if not df.empty:
        df_ranking = df.sort_values("Post_Score", ascending=False).head(10).copy()
        df_ranking["Post_Curto"] = df_ranking["Post"].apply(lambda p: truncar_texto(p, 30))

        fig_score = px.bar(
            df_ranking, x="Post_Score", y="Post_Curto", orientation="h",
            color="Tipo do post", color_discrete_sequence=PALETA,
            text=df_ranking["Post_Score"].round(1), hover_name="Post"
        )
        fig_score.update_traces(textposition="outside", cliponaxis=False)
        fig_score = estilo_padrao(fig_score, altura=max(340, 42 * len(df_ranking)),
                                   eixo_x_titulo="Score Composto (0-100)")
        fig_score.update_yaxes(title="", categoryorder="total ascending")
        fig_score.update_xaxes(range=[0, 108])
        st.plotly_chart(fig_score, width='stretch')

    st.markdown("---")

    st.subheader(":material/grid_view: Matriz de Quadrantes: Alcance x Engajamento")
    st.markdown(
        '<p class="section-caption">Cada post posicionado por Visualizações e Taxa de Engajamento. '
        'As linhas tracejadas marcam a mediana do grupo filtrado.</p>',
        unsafe_allow_html=True
    )
    if not df.empty and len(df) > 1:
        mediana_views = df["Visualizações"].median()
        mediana_engajamento = df["Taxa de engajamento"].median()

        fig_scatter = px.scatter(
            df, x="Visualizações", y="Taxa de engajamento",
            color="Tipo do post", size="Interações Totais",
            hover_name="Post", size_max=38, color_discrete_sequence=PALETA
        )
        fig_scatter.add_vline(x=mediana_views, line_dash="dash", line_color=COR_TEXTO_MUTED, opacity=0.6)
        fig_scatter.add_hline(y=mediana_engajamento, line_dash="dash", line_color=COR_TEXTO_MUTED, opacity=0.6)

        x_max, x_min = df["Visualizações"].max(), df["Visualizações"].min()
        y_max, y_min = df["Taxa de engajamento"].max(), df["Taxa de engajamento"].min()
        anotacoes = [
            dict(x=x_max, y=y_max, text="🚀 Virais", showarrow=False, xanchor="right", yanchor="top", font=dict(color=COR_VERDE, size=12)),
            dict(x=x_min, y=y_max, text="💎 Nicho Fiel", showarrow=False, xanchor="left", yanchor="top", font=dict(color=COR_AZUL, size=12)),
            dict(x=x_max, y=y_min, text="📢 Alcance Vazio", showarrow=False, xanchor="right", yanchor="bottom", font=dict(color=COR_LARANJA, size=12)),
            dict(x=x_min, y=y_min, text="⚠️ Baixa Performance", showarrow=False, xanchor="left", yanchor="bottom", font=dict(color=COR_TEXTO_MUTED, size=12)),
        ]
        fig_scatter = estilo_padrao(fig_scatter, altura=520,
                                     eixo_x_titulo="Visualizações", eixo_y_titulo="Taxa de Engajamento (%)")
        fig_scatter.update_layout(annotations=anotacoes)
        st.plotly_chart(fig_scatter, width='stretch')
    else:
        st.info("São necessários pelo menos 2 posts no filtro atual para montar a matriz de quadrantes.")

    st.markdown("---")

    col_pareto, col_cdf = st.columns(2, gap="large")

    with col_pareto:
        st.subheader(":material/leaderboard: Pareto de Interações")
        st.markdown('<p class="section-caption">Quantos posts concentram a maior parte do resultado (regra 80/20).</p>', unsafe_allow_html=True)
        if not df.empty:
            df_pareto = df.sort_values("Interações Totais", ascending=False).reset_index(drop=True)
            df_pareto["% Acumulado"] = df_pareto["Interações Totais"].cumsum() / df_pareto["Interações Totais"].sum() * 100
            df_pareto["Post_Curto"] = df_pareto["Post"].apply(lambda p: truncar_texto(p, 14))

            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(
                x=df_pareto["Post_Curto"], y=df_pareto["Interações Totais"],
                name="Interações Totais", marker_color=COR_AZUL,
                hovertext=df_pareto["Post"], hovertemplate="%{hovertext}<br>%{y:,.0f}<extra></extra>"
            ))
            fig_pareto.add_trace(go.Scatter(
                x=df_pareto["Post_Curto"], y=df_pareto["% Acumulado"],
                name="% Acumulado", mode="lines+markers",
                line=dict(color=COR_LARANJA, width=3), yaxis="y2"
            ))
            fig_pareto.add_hline(y=80, line_dash="dot", line_color=COR_TEXTO_MUTED, yref="y2")

            fig_pareto = estilo_padrao(fig_pareto, altura=440, rotacionar_x=True)
            fig_pareto.update_layout(
                yaxis=dict(title="Interações Totais", showgrid=True, gridcolor=COR_GRID),
                yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 105], showgrid=False),
                hovermode="x unified"
            )
            st.plotly_chart(fig_pareto, width='stretch')

            posts_para_80 = min((df_pareto["% Acumulado"] <= 80).sum() + 1, len(df_pareto))
            st.caption(
                f":material/insights: **{posts_para_80} de {len(df_pareto)} posts** "
                f"({posts_para_80 / len(df_pareto):.0%}) concentram 80% das interações."
            )

    with col_cdf:
        st.subheader(":material/monitoring: Distribuição Acumulada")
        st.markdown('<p class="section-caption">O resultado depende de poucos posts "hit" ou é consistente?</p>', unsafe_allow_html=True)
        if not df.empty:
            fig_cdf = px.ecdf(
                df, x="Visualizações",
                color="Tipo do post" if df["Tipo do post"].nunique() > 1 else None,
                color_discrete_sequence=PALETA, markers=True
            )
            fig_cdf = estilo_padrao(fig_cdf, altura=440, eixo_x_titulo="Visualizações")
            fig_cdf.update_yaxes(title="Proporção Acumulada", tickformat=".0%")
            st.plotly_chart(fig_cdf, width='stretch')

    st.markdown("---")

    col_radar, col_box = st.columns(2, gap="large")

    with col_radar:
        st.subheader(":material/radar: Radar por Formato")
        st.markdown('<p class="section-caption">Médias estratégicas comparadas entre formatos de publicação.</p>', unsafe_allow_html=True)
        eixos_radar = ["Taxa de Atração", "Taxa de engajamento", "Fator de Retenção e Viralidade", "Taxa de Conversão de Perfil (%)"]
        formatos_presentes = df["Tipo do post"].dropna().unique()

        if len(formatos_presentes) > 0:
            fig_radar = go.Figure()
            for i, formato in enumerate(formatos_presentes):
                df_formato = df[df["Tipo do post"] == formato]
                medias = [df_formato[eixo].mean() for eixo in eixos_radar]
                fig_radar.add_trace(go.Scatterpolar(
                    r=medias + [medias[0]], theta=eixos_radar + [eixos_radar[0]],
                    fill='toself', name=formato, line_color=PALETA[i % len(PALETA)], opacity=0.65
                ))
            fig_radar = estilo_padrao(fig_radar, altura=460)
            fig_radar.update_layout(polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(visible=True, showticklabels=True, gridcolor=COR_GRID)
            ))
            st.plotly_chart(fig_radar, width='stretch')

    with col_box:
        st.subheader(":material/bar_chart: Consistência do Engajamento")
        st.markdown('<p class="section-caption">Dispersão e mediana da taxa de engajamento por formato.</p>', unsafe_allow_html=True)
        if not df.empty:
            fig_box = px.box(
                df, x="Tipo do post", y="Taxa de engajamento", color="Tipo do post",
                points="all", color_discrete_sequence=PALETA
            )
            fig_box = estilo_padrao(fig_box, altura=460, legenda=False, eixo_y_titulo="Taxa de Engajamento (%)")
            fig_box.update_xaxes(title="")
            st.plotly_chart(fig_box, width='stretch')

# ---------------------------------------------------------
# ABA 3 — FUNIL DE CONVERSÃO
# ---------------------------------------------------------
with aba_funil:
    st.subheader(":material/filter_alt: Funil de Conversão do Público")
    st.markdown(
        '<p class="section-caption">Evolução da jornada do usuário: Visualizações ➔ Visitas ao Perfil ➔ Novos Seguidores</p>',
        unsafe_allow_html=True
    )

    if not df.empty:
        funil_valores = [df["Visualizações"].sum(), df["Visitas ao perfil"].sum(), df["Seguidores novos"].sum()]
        funil_labels = ["Visualizações", "Visitas ao Perfil", "Seguidores Novos"]

        fig_funil = go.Figure(go.Funnel(
            y=funil_labels, x=funil_valores,
            textinfo="value+percent initial", marker={"color": PALETA}
        ))
        fig_funil = estilo_padrao(fig_funil, altura=440, legenda=False)
        st.plotly_chart(fig_funil, width='stretch')

    st.markdown("---")

    st.subheader(":material/calculate: Simulador de Metas")
    st.markdown(
        '<p class="section-caption">Baseado na taxa de conversão de perfil média do período filtrado. '
        'Ajuste a meta na barra lateral.</p>',
        unsafe_allow_html=True
    )
    meta_col1, meta_col2, meta_col3 = st.columns(3, gap="medium")
    with meta_col1:
        st.markdown(
            f"""<div class="meta-card"><div class="kpi-title">Meta de Seguidores</div>
            <div class="kpi-value">{meta_novos_seguidores}</div></div>""",
            unsafe_allow_html=True
        )
    with meta_col2:
        st.markdown(
            f"""<div class="meta-card"><div class="kpi-title">Taxa de Conversão Atual</div>
            <div class="kpi-value">{tx_conversao_media:.2f}%</div></div>""",
            unsafe_allow_html=True
        )
    with meta_col3:
        valor_visitas = f"{visitas_necessarias:,.0f}".replace(",", ".") if visitas_necessarias else "—"
        st.markdown(
            f"""<div class="meta-card" style="border-left:4px solid {COR_VERDE};">
            <div class="kpi-title">Visitas ao Perfil Necessárias</div>
            <div class="kpi-value">{valor_visitas}</div></div>""",
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# ABA 4 — DADOS E EXPORTAÇÃO
# ---------------------------------------------------------
with aba_dados:
    st.subheader(":material/table_chart: Tabela Completa de Dados")
    st.markdown('<p class="section-caption">Base filtrada conforme os controles da barra lateral.</p>', unsafe_allow_html=True)

    colunas_exibicao = [
        "Post", "Tipo do post", "Visualizações", "Curtidas", "Comentários",
        "Interações Totais", "Visitas ao perfil", "Seguidores novos",
        "Taxa de engajamento", "Taxa de Conversão de Perfil (%)",
        "Taxa_Amplificacao_Calc", "Taxa_Salvamento_Calc", "Taxa_Comentario_Calc",
        "Post_Score", "Anomalia"
    ]
    colunas_presentes = [c for c in colunas_exibicao if c in df.columns]

    st.dataframe(
        df[colunas_presentes].rename(columns={
            "Taxa_Amplificacao_Calc": "Taxa de Amplificação (%)",
            "Taxa_Salvamento_Calc": "Taxa de Salvamento (%)",
            "Taxa_Comentario_Calc": "Taxa de Comentário (%)",
            "Post_Score": "Score Composto"
        }).style.format({
            "Taxa de engajamento": "{:.2f}%",
            "Taxa de Conversão de Perfil (%)": "{:.2f}%",
            "Taxa de Amplificação (%)": "{:.2f}%",
            "Taxa de Salvamento (%)": "{:.2f}%",
            "Taxa de Comentário (%)": "{:.2f}%",
            "Score Composto": "{:.1f}"
        }, na_rep="-"),
        width='stretch',
        height=460
    )

    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=":material/download: Baixar Dados Filtrados (CSV)",
        data=csv_data,
        file_name="byron_data_engine_export.csv",
        mime="text/csv"
    )

st.markdown("---")
st.caption("Byron Data Engine © • Desenvolvido para inteligência de dados de marketing.")