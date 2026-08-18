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
# AUTENTICAÇÃO (Google OIDC) — acesso restrito ao domínio da empresa júnior
# =========================================================
# Troque pelo domínio de e-mail institucional dos membros, ex: "ejunifei.com.br"
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

# Usuário autenticado e autorizado — mostra quem está logado e opção de sair
with st.sidebar:
    st.markdown(f":material/account_circle: Logado como **{st.user.email}**")
    st.button(":material/logout: Sair", on_click=st.logout)
    st.markdown("---")

# =========================================================
# LINKS DOS CSVs (SUBSTITUA PELAS SUAS URLs PÚBLICAS DO GOOGLE SHEETS)
# =========================================================
LINK_COMERCIAL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3_WYtPMw6Ll4S38ApBIC04x4cTzp2SPHyBzvR5Evk_gSkd1rN2oYxP86JLcdOd1cH7-B2OfOcByjz/pub?gid=1889107330&single=true&output=csv" 
LINK_ACADEMICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT3_WYtPMw6Ll4S38ApBIC04x4cTzp2SPHyBzvR5Evk_gSkd1rN2oYxP86JLcdOd1cH7-B2OfOcByjz/pub?gid=544047503&single=true&output=csv"
# =========================================================
# FUNÇÃO DE CARGA E TRATAMENTO DOS DADOS
# =========================================================
@st.cache_data
def carregar_dados(url):
    df = pd.read_csv(url)

    # Colunas que vêm no padrão brasileiro (vírgula decimal) -> float * 100
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

    # Coluna calculada: Interações Totais
    colunas_interacao = [
        "Curtidas", "Comentários", "Reposts",
        "Compartilhamentos", "Salvamentos"
    ]
    for col in colunas_interacao:
        if col not in df.columns:
            df[col] = 0

    df["Interações Totais"] = df[colunas_interacao].sum(axis=1)

    return df


def remover_outliers_iqr(df, coluna):
    """Remove outliers de uma coluna numérica usando a regra do IQR (1.5x)."""
    q1 = df[coluna].quantile(0.25)
    q3 = df[coluna].quantile(0.75)
    iqr = q3 - q1
    limite_superior = q3 + 1.5 * iqr
    limite_inferior = q1 - 1.5 * iqr
    return df[(df[coluna] >= limite_inferior) & (df[coluna] <= limite_superior)]


# =========================================================
# SIDEBAR
# =========================================================
st.sidebar.title(":material/tune: Configurações")

modo = st.sidebar.radio(
    "Qual contexto você quer analisar agora?",
    ["Comercial (Prospecção B2B)", "Acadêmico (Comunidade UNIFEI)"]
)

filtrar_outliers = st.sidebar.checkbox(
    ":material/shield: Filtrar outliers (eventos atípicos)",
    value=False,
    help="Remove posts com pico de Visualizações fora do padrão estatístico (regra do IQR), "
         "evitando que um único viral distorça as médias analisadas."
)

if st.sidebar.button(":material/refresh: Atualizar dados agora"):
    st.cache_data.clear()
    st.sidebar.success("Prontinho! Cache limpo — os dados serão recarregados na próxima consulta.")

st.sidebar.markdown("---")
st.sidebar.caption("Byron Data Engine • Seu painel de inteligência de marketing orgânico")

# Define URL e títulos de acordo com o modo escolhido
if modo.startswith("Comercial"):
    url_dados = LINK_COMERCIAL
    titulo_principal = ":material/query_stats: Byron Data Engine — Funil Comercial"
    subtitulo = "Como o conteúdo orgânico está performando na geração de leads e na prospecção de clientes B2B."
else:
    url_dados = LINK_ACADEMICO
    titulo_principal = ":material/school: Byron Data Engine — Funil Acadêmico (Comunidade UNIFEI)"
    subtitulo = "Como o conteúdo orgânico está engajando a comunidade acadêmica da UNIFEI."

# =========================================================
# CARREGAMENTO E FILTRAGEM DOS DADOS
# =========================================================
df_bruto = carregar_dados(url_dados)

if filtrar_outliers:
    df = remover_outliers_iqr(df_bruto, "Visualizações")
    qtd_removidos = len(df_bruto) - len(df)
else:
    df = df_bruto.copy()
    qtd_removidos = 0

# =========================================================
# CABEÇALHO
# =========================================================
st.title(titulo_principal)
st.markdown(f"##### {subtitulo}")

if filtrar_outliers:
    st.info(
        f":material/shield: Filtro de outliers ativo — {qtd_removidos} post(s) atípico(s) "
        f"foram deixados de fora da análise (regra do IQR sobre 'Visualizações')."
    )

st.markdown("---")

# =========================================================
# TOP SCORECARDS
# =========================================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label=":material/visibility: Visualizações totais",
        value=f"{df['Visualizações'].sum():,.0f}".replace(",", ".")
    )

with col2:
    st.metric(
        label=":material/bolt: Engajamento médio",
        value=f"{df['Taxa de engajamento'].mean():.2f}%"
    )

with col3:
    st.metric(
        label=":material/sync_alt: Conversão média do perfil",
        value=f"{df['Taxa de Conversão de Perfil (%)'].mean():.2f}%"
    )

with col4:
    st.metric(
        label=":material/rocket_launch: Novos seguidores",
        value=f"{df['Seguidores novos'].sum():,.0f}".replace(",", ".")
    )

st.markdown("---")

# =========================================================
# LEADERBOARD DINÂMICO (TOP PERFORMERS)
# =========================================================
st.subheader(":material/trophy: Destaques do período")
st.caption("Os posts que mais se destacaram em cada frente — vale estudar o que funcionou neles.")

top_engajamento = df.loc[df["Taxa de engajamento"].idxmax()]
top_conversao = df.loc[df["Taxa de Conversão de Perfil (%)"].idxmax()]
top_retencao = df.loc[df["Fator de Retenção e Viralidade"].idxmax()]

lb1, lb2, lb3 = st.columns(3)

with lb1:
    st.markdown(
        f"""
        <div style="background-color:#1E293B; padding:20px; border-radius:12px; text-align:center; border:1px solid {COR_AZUL};">
            <p style="font-size:14px; color:#A5B4FC; margin-bottom:4px;">MAIOR ENGAJAMENTO</p>
            <p style="font-size:20px; color:white; font-weight:bold; margin-bottom:2px;">{top_engajamento['Post']}</p>
            <p style="font-size:28px; color:{COR_AZUL}; font-weight:bold; margin-top:6px;">{top_engajamento['Taxa de engajamento']:.2f}%</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with lb2:
    st.markdown(
        f"""
        <div style="background-color:#1E293B; padding:20px; border-radius:12px; text-align:center; border:1px solid {COR_LARANJA};">
            <p style="font-size:14px; color:#A5B4FC; margin-bottom:4px;">MAIOR CONVERSÃO DE PERFIL</p>
            <p style="font-size:20px; color:white; font-weight:bold; margin-bottom:2px;">{top_conversao['Post']}</p>
            <p style="font-size:28px; color:{COR_LARANJA}; font-weight:bold; margin-top:6px;">{top_conversao['Taxa de Conversão de Perfil (%)']:.2f}%</p>
        </div>
        """,
        unsafe_allow_html=True
    )

with lb3:
    st.markdown(
        f"""
        <div style="background-color:#1E293B; padding:20px; border-radius:12px; text-align:center; border:1px solid {COR_VERDE};">
            <p style="font-size:14px; color:#A5B4FC; margin-bottom:4px;">MAIOR RETENÇÃO E VIRALIDADE</p>
            <p style="font-size:20px; color:white; font-weight:bold; margin-bottom:2px;">{top_retencao['Post']}</p>
            <p style="font-size:28px; color:{COR_VERDE}; font-weight:bold; margin-top:6px;">{top_retencao['Fator de Retenção e Viralidade']:.2f}%</p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# =========================================================
# GRÁFICO 1 — FUNIL DE CONVERSÃO
# =========================================================
st.subheader(":material/filter_alt: Funil de conversão do público")

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
fig_funil.update_layout(height=500, margin=dict(t=30, b=30))

st.plotly_chart(fig_funil, use_container_width=True)

st.markdown("---")

# =========================================================
# GRÁFICO 2 — MATRIZ ESTRATÉGICA (DISPERSÃO)
# =========================================================
st.subheader(":material/my_location: Matriz estratégica: alcance x engajamento")
st.caption("Quanto mais para cima e para a direita, melhor o post equilibrou alcance e engajamento.")

fig_scatter = px.scatter(
    df,
    x="Visualizações",
    y="Taxa de engajamento",
    color="Tipo do post",
    size="Interações Totais",
    hover_name="Post",
    size_max=50,
    color_discrete_sequence=PALETA
)
fig_scatter.update_layout(height=500, margin=dict(t=30, b=30))

st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# =========================================================
# GRÁFICO 3 — RADAR (TEIA DE ARANHA) POR FORMATO
# =========================================================
st.subheader(":material/radar: Radar de performance por formato")

eixos_radar = [
    "Taxa de Atração",
    "Taxa de engajamento",
    "Fator de Retenção e Viralidade",
    "Taxa de Conversão de Perfil (%)"
]

formatos_alvo = ["Reel", "Carrossel", "Post Único"]
formatos_presentes = [f for f in formatos_alvo if f in df["Tipo do post"].unique()]

if len(formatos_presentes) == 0:
    st.warning(
        ":material/warning: Nenhum dos formatos padrão (Reel, Carrossel, Post Único) foi "
        "encontrado na coluna 'Tipo do post' — vale checar se os nomes batem com a planilha."
    )
else:
    fig_radar = go.Figure()

    for i, formato in enumerate(formatos_presentes):
        df_formato = df[df["Tipo do post"] == formato]
        medias = [df_formato[eixo].mean() for eixo in eixos_radar]

        fig_radar.add_trace(go.Scatterpolar(
            r=medias + [medias[0]],  # fecha o polígono
            theta=eixos_radar + [eixos_radar[0]],
            fill='toself',
            name=formato,
            line_color=PALETA[i % len(PALETA)],
            opacity=0.7
        ))

    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, showticklabels=True)
        ),
        height=550,
        margin=dict(t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
    )

    st.plotly_chart(fig_radar, use_container_width=True)

st.markdown("---")

# =========================================================
# GRÁFICO 4 — LINHAS: ATRAÇÃO x RETENÇÃO
# =========================================================
st.subheader(":material/trending_up: Evolução: taxa de atração x fator de retenção e viralidade")

fig_linhas = go.Figure()

fig_linhas.add_trace(go.Scatter(
    x=df["Post"],
    y=df["Taxa de Atração"],
    mode="lines+markers",
    name="Taxa de Atração",
    line=dict(color=COR_AZUL)
))

fig_linhas.add_trace(go.Scatter(
    x=df["Post"],
    y=df["Fator de Retenção e Viralidade"],
    mode="lines+markers",
    name="Fator de Retenção e Viralidade",
    line=dict(color=COR_LARANJA)
))

fig_linhas.update_layout(
    height=500,
    margin=dict(t=30, b=30),
    xaxis_title="Post",
    yaxis_title="Percentual (%)"
)

st.plotly_chart(fig_linhas, use_container_width=True)

st.markdown("---")

# =========================================================
# GRÁFICO 5 — BOXPLOT DE CONSISTÊNCIA ESTATÍSTICA
# =========================================================
st.subheader(":material/analytics: Consistência estatística do engajamento por formato")
st.caption(
    "O boxplot mostra a dispersão e a mediana real de cada formato, evitando a "
    "ilusão de desempenho causada por médias simples distorcidas por outliers."
)

fig_box = px.box(
    df,
    x="Tipo do post",
    y="Taxa de engajamento",
    color="Tipo do post",
    points="all",
    color_discrete_sequence=PALETA
)
fig_box.update_layout(height=500, margin=dict(t=30, b=30), showlegend=False)

st.plotly_chart(fig_box, use_container_width=True)

st.markdown("---")
st.caption("Byron Data Engine © .")