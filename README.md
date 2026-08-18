# Byron Data Engine

Painel de inteligência de marketing orgânico, desenvolvido em Streamlit, com dois contextos de análise (Comercial e Acadêmico) e acesso restrito aos membros da empresa júnior via login com Google.

---

## Sumário

- [Visão geral](#visão-geral)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como funciona o painel](#como-funciona-o-painel)
- [Fonte de dados](#fonte-de-dados)
- [Autenticação (login com Google)](#autenticação-login-com-google)
- [Configuração para rodar localmente](#configuração-para-rodar-localmente)
- [Deploy no Streamlit Community Cloud](#deploy-no-streamlit-community-cloud)
- [Paleta de cores e identidade visual](#paleta-de-cores-e-identidade-visual)
- [Problemas conhecidos e soluções](#problemas-conhecidos-e-soluções)
- [Manutenção e próximos passos](#manutenção-e-próximos-passos)

---

## Visão geral

O **Byron Data Engine** consome dados de duas planilhas do Google Sheets (publicadas como CSV) e apresenta métricas de performance de conteúdo orgânico em dois contextos:

- **Comercial (Prospecção B2B):** foco em geração de leads e prospecção de clientes.
- **Acadêmico (Comunidade UNIFEI):** foco em engajamento com a comunidade acadêmica.

O acesso ao painel é restrito: apenas contas Google do domínio `@byronsolutions.com` conseguem entrar.

---

## Estrutura do projeto

```
.
├── dashboardByron.py       # Código principal do painel (Streamlit)
├── requirements.txt        # Dependências Python
└── .streamlit/
    └── secrets.toml        # Credenciais (NUNCA versionar no Git)
```

> `secrets.toml` não deve ser commitado no repositório. No Streamlit Community Cloud, ele é configurado direto em **App → Settings → Secrets**.

---

## Como funciona o painel

1. **Sidebar:** escolha do contexto (Comercial/Acadêmico), filtro de outliers (regra do IQR sobre `Visualizações`) e botão para limpar o cache de dados.
2. **Scorecards:** visualizações totais, engajamento médio, conversão média de perfil e novos seguidores.
3. **Destaques do período:** os posts com maior engajamento, maior conversão de perfil e maior retenção/viralidade.
4. **Funil de conversão:** Visualizações → Visitas ao Perfil → Seguidores Novos.
5. **Matriz estratégica:** dispersão entre alcance (Visualizações) e engajamento, com o tamanho da bolha representando interações totais.
6. **Radar de performance:** compara os formatos Reel, Carrossel e Post Único em quatro eixos (atração, engajamento, retenção/viralidade, conversão de perfil).
7. **Evolução temporal:** taxa de atração x fator de retenção e viralidade, post a post.
8. **Boxplot de consistência:** dispersão real do engajamento por formato, evitando distorções causadas por outliers.

---

## Fonte de dados

Os dados vêm de planilhas do Google Sheets publicadas como CSV:

```python
LINK_COMERCIAL = "https://docs.google.com/spreadsheets/d/e/..."
LINK_ACADEMICO = "https://docs.google.com/spreadsheets/d/e/..."
```

Para publicar uma planilha como CSV: **Arquivo → Compartilhar → Publicar na Web → selecionar a aba → formato CSV**.

Colunas esperadas na planilha (nomes exatos, sensíveis a maiúsculas/acentos):

| Coluna | Tipo | Observação |
|---|---|---|
| `Post` | texto | identificador/nome do post |
| `Tipo do post` | texto | `Reel`, `Carrossel` ou `Post Único` |
| `Visualizações` | número | |
| `Visitas ao perfil` | número | |
| `Seguidores novos` | número | |
| `Taxa de engajamento` | decimal BR (`0,05`) | convertida para `%` automaticamente |
| `Taxa de Conversão de Perfil (%)` | decimal BR | convertida para `%` automaticamente |
| `Taxa de Atração` | decimal BR | convertida para `%` automaticamente |
| `Fator de Retenção e Viralidade` | decimal BR | convertida para `%` automaticamente |
| `Curtidas`, `Comentários`, `Reposts`, `Compartilhamentos`, `Salvamentos` | número | somados em `Interações Totais` |

O cache dos dados (`@st.cache_data`) pode ser limpo manualmente pelo botão **"Atualizar dados agora"** na sidebar.

---

## Autenticação (login com Google)

O painel usa a autenticação nativa do Streamlit (`st.login()` / `st.user`), baseada em OIDC, com o Google como provedor de identidade. Apenas e-mails que terminam em `@byronsolutions.com` têm acesso liberado; qualquer outro domínio recebe uma tela de "acesso não autorizado".

Fluxo no código:

1. Se `st.user.is_logged_in` for `False`, mostra a tela de login com o botão "Entrar com Google".
2. Após o login, verifica se `st.user.email` termina com `@byronsolutions.com`.
3. Se não bater, bloqueia o acesso e oferece a opção de sair (`st.logout`).
4. Se bater, libera o painel e mostra o e-mail logado + botão de logout na sidebar.

### Credenciais necessárias (Google Cloud Console)

1. Acesse [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials).
2. Crie um **OAuth Client ID** do tipo **Web application**.
3. Em **Authorized redirect URIs**, cadastre:
   - Produção: `https://dashboardbyron.streamlit.app/oauth2callback`
   - Local (opcional, para testes): `http://localhost:8501/oauth2callback`
4. Guarde o **Client ID** e o **Client Secret** gerados.

### Arquivo `secrets.toml`

```toml
[auth]
redirect_uri = "https://dashboardbyron.streamlit.app/oauth2callback"
cookie_secret = "string-aleatoria-gerada-uma-unica-vez"
client_id = "SEU_CLIENT_ID.apps.googleusercontent.com"
client_secret = "SEU_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

> As credenciais ficam achatadas direto em `[auth]` (sem `[auth.google]`) porque o código chama `st.login()` sem especificar o nome do provedor. Se um segundo provedor for adicionado no futuro, é preciso usar `[auth.google]` + `st.login("google")`.

Para gerar um `cookie_secret` seguro:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

⚠️ **Nunca** commitar o `secrets.toml` com valores reais no GitHub. No Streamlit Community Cloud, ele é colado em **App → Settings → Secrets**.

---

## Configuração para rodar localmente

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd <pasta-do-projeto>

# 2. Criar ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Criar .streamlit/secrets.toml localmente (não versionar)
#    com redirect_uri = "http://localhost:8501/oauth2callback"

# 5. Rodar
streamlit run dashboardByron.py
```

---

## Deploy no Streamlit Community Cloud

1. Suba o projeto para um repositório no GitHub (sem o `secrets.toml`).
2. Em [share.streamlit.io](https://share.streamlit.io), clique em **New app**, selecione o repositório, branch e o arquivo principal (`dashboardByron.py`).
3. Faça o primeiro deploy — nesse momento a autenticação pode aparecer como "não configurada" até os secrets serem preenchidos, sem quebrar o app.
4. Copie a URL final do app (ex: `https://dashboardbyron.streamlit.app`).
5. Volte no Google Cloud Console e confirme que o **Authorized redirect URI** bate exatamente com `https://dashboardbyron.streamlit.app/oauth2callback`.
6. Em **App → Settings → Secrets**, cole o conteúdo do `secrets.toml` (seção acima).
7. O app reinicia automaticamente e o login passa a ser exigido.

### Publicar o app OAuth para todo o domínio

Se a tela de consentimento OAuth estiver como **"Testing"** no Google Cloud, só e-mails cadastrados manualmente como *test users* conseguem logar (limite de 100). Para liberar automaticamente todo mundo do domínio:

- Se a empresa júnior usa **Google Workspace**: configure a tela de consentimento como **"Internal"**.
- Caso contrário: clique em **"Publish App"** na tela de consentimento OAuth.

---

## Paleta de cores e identidade visual

| Cor | Hex | Uso |
|---|---|---|
| 🔵 Azul | `#2D9FE0` | Engajamento, atração, elemento primário |
| 🟠 Laranja | `#D46A2E` | Conversão, retenção |
| 🟢 Verde-água | `#28DCBD` | Retenção/viralidade, terceiro elemento da paleta |

Ícones usam a sintaxe nativa `:material/nome_do_icone:` do Streamlit (requer Streamlit ≥ 1.31 para renderizar corretamente).

---

## Problemas conhecidos e soluções

| Erro | Causa | Solução |
|---|---|---|
| `AttributeError: st.user has no attribute "is_logged_in"` | `secrets.toml` sem a seção `[auth]` configurada ainda | Configurar os secrets ou aguardar — o código já trata esse caso com `getattr` |
| `StreamlitMissingAuthlibError` | Pacote `Authlib` ausente | Adicionar `Authlib>=1.3.2` ao `requirements.txt` |
| `StreamlitAuthError` | Credenciais dentro de `[auth.google]` mas código chama `st.login()` sem provedor | Achatar as credenciais direto em `[auth]` |
| `ModuleNotFoundError: No module named 'httpx'` | `httpx` não instalado como dependência do Authlib | Adicionar `httpx` ao `requirements.txt` |
| Planilha "Comercial" não carregava | Comparação `if modo == "Comercial"` não batia com o texto completo do radio button | Corrigido para `modo.startswith("Comercial")` |

---

## Manutenção e próximos passos

- **Rotacionar credenciais:** se o `client_secret` do Google ou o `cookie_secret` vazarem, gere novos valores imediatamente (Google Cloud Console → Credentials, e um novo `token_hex` para o cookie).
- **Adicionar novos membros:** não é necessário nenhum cadastro manual — qualquer conta `@byronsolutions.com` já tem acesso automático (a menos que a tela de consentimento OAuth ainda esteja em modo "Testing", ver seção acima).
- **Trocar/atualizar planilhas:** basta substituir `LINK_COMERCIAL` e `LINK_ACADEMICO` no código e limpar o cache pelo botão da sidebar.
- **Possíveis evoluções futuras:** exportação dos gráficos em PDF, filtro por período de datas, múltiplos provedores de login (ex: Microsoft) usando `st.login("google")` / `st.login("microsoft")`.