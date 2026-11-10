# 00. Varredura do projecto (inventário)

Este ficheiro resume o levantamento completo do código real do projecto
**Pedidos de Documentos · UCM-FEG**. Todos os factos são extraídos dos
ficheiros existentes; nada é inventado.

## 1. Identificação do projecto

| Campo | Valor |
| --- | --- |
| Nome | Pedidos de Documentos · UCM-FEG |
| Contexto | Faculdade de Economia e Gestão da Universidade Católica de Moçambique (UCM-FEG) |
| Linguagem | Python 3.12+ |
| Framework | Django 6.1.3 (`requirements.txt` linha 6) |
| Base de dados | SQLite 3 (`config/settings.py` linha 135, `django.db.backends.sqlite3`) |
| Ficheiro de configuração | `config/settings.py` |
| Entrada da aplicação | `manage.py` (`DJANGO_SETTINGS_MODULE=config.settings`) |
| WSGI | `config/wsgi.py` |
| ASGI | `config/asgi.py` |
| URLs raiz | `config/urls.py` (`ROOT_URLCONF`) |

## 2. Dependências principais (`requirements.txt`)

| Pacote | Versão | Função |
| --- | --- | --- |
| Django | 6.1.3 | Framework Web |
| django-allauth | 65.21.1 | Autenticação e login social (Google) |
| asgiref | 3.13.0 | Interface ASGI |
| cryptography | 50.0.2 | Criptografia (usada por Django/allauth) |
| oauthlib | 4.0.1 | OAuth (login Google) |
| PyJWT | 2.15.1 | JSON Web Tokens (allauth) |
| requests | 2.34.2 | Requisições HTTP (allauth/social) |
| sqlparse | 0.6.1 | Parsing SQL |

**Nota:** `django-tailwind-cli` (v4.8.2, ambiente `.venv`) está instalado e listado em
`INSTALLED_APPS` (`config/settings.py`), mas **não consta de `requirements.txt`** (deduzido
da comparação do ficheiro com `pip show django-tailwind-cli`). O CSS é compilado com o
binário Tailwind CLI (`static/tailwindcss`, não rastreado no Git) a partir de
`static/css/input.css` para `static/css/app.css`.

## 3. Estrutura de pastas (comentada)

```
requerimentos/
├── config/                 # Pacote de configuração do Django (settings, urls, wsgi, asgi)
│   ├── settings.py         # Configurações globais (segurança, DB, cache, email, taxas, Tailwind)
│   ├── urls.py             # URLs raiz do projecto
│   ├── wsgi.py             # Ponto de entrada WSGI
│   └── asgi.py             # Ponto de entrada ASGI
├── contas/                 # App: contas, perfis, autenticação, cursos
│   ├── models.py           # Curso, Perfil, extrair_numero_estudante
│   ├── views.py            # LoginViewComLimite, dashboard_redirect, completar_perfil
│   ├── urls.py             # URLs da app contas (login, logout, completar-perfil)
│   ├── permissoes.py       # Decoradores de papel (estudante_required, secretaria_required, etc.)
│   ├── middleware.py       # CompletarPerfilMiddleware (obriga perfil completo do estudante)
│   ├── adapters.py         # ContasSocialAccountAdapter (valida domínio Google)
│   ├── context_processors.py # google_oauth, atendimento_presencial
│   ├── signals.py          # Cria Perfil automaticamente ao criar User
│   ├── forms.py            # CompletarPerfilForm
│   ├── admin.py            # Registo de Perfil e Curso no admin
│   ├── management/         # Comandos: carregar_cursos, importar_utilizadores
│   └── testes: tests.py, test_fase4.py, test_urls.py
├── pedidos/                # App: pedidos de documentos, tipos, anexos, decisões
│   ├── models.py           # TipoDocumento, Pedido, Anexo, Decisao
│   ├── views.py            # Views de pedidos, fila, painel, serviços de staff
│   ├── urls.py             # URLs da app pedidos
│   ├── services.py         # Regras de negócio (aprovar, indeferir, marcar_pronto, marcar_entregue)
│   ├── notificacoes.py     # Envio de email ao estudante (pronto / indeferido)
│   ├── validators.py       # Validação de anexos (extensão, tamanho, assinatura binária)
│   ├── forms.py            # NovoPedidoForm
│   ├── admin.py            # Registo só-leitura de Pedido, Anexo, Decisão, TipoDocumento
│   ├── management/         # Comandos: fazer_backup, seed_demo
│   └── testes: tests.py, test_fase3.py, test_fase4.py
├── templates/              # Templates Django (herdam de base.html)
│   ├── base.html           # Layout base: sidebar fixa + topbar, Tailwind + Unpoly
│   ├── 403.html, 404.html, 500.html # Páginas de erro temáticas
│   ├── components/         # Componentes reutilizáveis (icon.html, table_wrap*.html)
│   │   ├── icon.html       # Ícones Lucide SVG embutidos
│   │   ├── table_wrap.html, table_wrap_open.html, table_wrap_close.html # Tabelas com scroll
│   ├── contas/             # home, login, completar_perfil, bloqueio_numero
│   ├── pedidos/            # novo_pedido, meus_pedidos, pedido_detalhe, fila, pesquisa,
│   │                       # pedido_staff_detalhe, painel, _resumo_pedido
│   └── _paginacao.html     # Componente de paginação reutilizável
├── static/                 # Ficheiros estáticos (CSS, fontes, imagens, vendor)
│   ├── css/input.css       # CSS de entrada do Tailwind (tokens, camadas)
│   ├── css/app.css         # CSS compilado (Tailwind v4, minificado) — gerado via tailwind CLI
│   ├── css/ucm-theme.css   # Tema visual UCM-FEG (mantido, não referenciado por base.html)
│   ├── fonts/              # Fonte Inter local (4 variantes .woff2)
│   │   ├── Inter-Regular.woff2, Inter-Medium.woff2, Inter-SemiBold.woff2, Inter-Bold.woff2
│   ├── img/logo-ucm.png    # Logótipo UCM
│   ├── vendor/unpoly/      # Unpoly JS + CSS (interacção parcial, substitui HTMX)
│   ├── vendor/bootstrap/   # Bootstrap 5 (ficheiros físicos mantidos, NÃO referenciados)
│   ├── vendor/bootstrap-icons/ # Bootstrap Icons (mantido, NÃO referenciado)
│   ├── vendor/chartjs/     # Chart.js (usado no painel, não alvo da migração)
│   └── tailwindcss         # Binário Tailwind CLI (não rastreado no Git)
├── media/                  # Anexes enviados (não servido publicamente)
├── db.sqlite3              # Base de dados SQLite de desenvolvimento
├── manage.py               # Utilitário de linha de comandos do Django
├── requirements.txt        # Dependências Python
├── tailwind.config.js      # Tokens de design Tailwind (marca UCM, cores por estado)
├── README.md               # Documentação de utilizador
├── test_mobile_playwright.py # Teste Playwright mobile/desktop (não é teste Django)
└── docs/                   # Dossier técnico (este documento)
```

## 4. Apps Django instaladas (`INSTALLED_APPS`)

- `django.contrib.admin`, `auth`, `contenttypes`, `sessions`, `messages`, `staticfiles`, `sites`
- `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`
- `contas` (app própria)
- `pedidos` (app própria)

(`config/settings.py` linhas 72-86)

## 5. Middleware (`config/settings.py` linhas 90-100)

1. `django.middleware.security.SecurityMiddleware`
2. `django.contrib.sessions.middleware.SessionMiddleware`
3. `django.middleware.common.CommonMiddleware`
4. `django.middleware.csrf.CsrfViewMiddleware`
5. `django.contrib.auth.middleware.AuthenticationMiddleware`
6. `django.contrib.messages.middleware.MessageMiddleware`
7. `django.middleware.clickjacking.XFrameOptionsMiddleware`
8. `allauth.account.middleware.AccountMiddleware`
9. `contas.middleware.CompletarPerfilMiddleware` (personalizado)

## 6. Backends de autenticação (`config/settings.py` linhas 102-105)

- `django.contrib.auth.backends.ModelBackend` (clássico: username/password)
- `allauth.account.auth_backends.AuthenticationBackend` (social)

## 7. Modelos (`contas/models.py` e `pedidos/models.py`)

### App `contas`

| Modelo | Ficheiro | Linhas aproximadas | Descrição |
| --- | --- | --- | --- |
| `Curso` | `contas/models.py` | 29-54 | Curso de estudo, com grau e activo |
| `Perfil` | `contas/models.py` | 57-153 | Perfil do utilizador: papel, número de estudante, curso, grau, telefone |

### App `pedidos`

| Modelo | Ficheiro | Linhas aproximadas | Descrição |
| --- | --- | --- | --- |
| `TipoDocumento` | `pedidos/models.py` | 25-67 | Tipo de documento com taxas por grau, IVA, prazo |
| `Pedido` | `pedidos/models.py` | 82-189 | Requerimento de documento (protocolo, estado, etapa, valor) |
| `Anexo` | `pedidos/models.py` | 192-227 | Ficheiro anexado a um pedido (BI, comprovativo, extracto, outro) |
| `Decisao` | `pedidos/models.py` | 234-283 | Decisão imutável sobre um pedido (etapa, resultado, justificação) |

## 8. Views / rotas

### App `contas` (`contas/views.py`, `contas/urls.py`)

| View | URL | Nome | Papéis | Descrição |
| --- | --- | --- | --- | --- |
| `LoginViewComLimite` | `/contas/login/` | `contas:login` | Público | Login clássico com limite de tentativas |
| `LogoutView` (allauth) | `/contas/logout/` | `contas:logout` | Autenticado | Terminar sessão |
| `completar_perfil` | `/contas/completar-perfil/` | `contas:completar_perfil` | Estudante | Completar dados académicos (curso) |
| `dashboard_redirect` | `/` | `home` | Autenticado | Página inicial por papel |

### App `pedidos` (`pedidos/views.py`, `pedidos/urls.py`)

| View | URL | Nome | Papéis | Descrição |
| --- | --- | --- | --- | --- |
| `novo_pedido` | `/pedidos/novo/` | `pedidos:novo_pedido` | Estudante | Submeter novo pedido com anexos |
| `meus_pedidos` | `/pedidos/meus/` | `pedidos:meus_pedidos` | Estudante | Listar pedidos próprios (paginados) |
| `resumo_pedido` | `/pedidos/resumo/` | `pedidos:resumo_pedido` | Estudante | Endpoint de resumo da taxa (alvo Unpoly `up-target`, substitui HTMX) |
| `anexo_download` | `/pedidos/anexo/<pk>/` | `pedidos:anexo_download` | Vários | Descarregar anexo com verificação de permissões |
| `pedido_detalhe` | `/pedidos/<pk>/` | `pedidos:pedido_detalhe` | Estudante (dono) | Ver detalhe do próprio pedido |
| `fila` | `/pedidos/staff/fila/` | `pedidos:fila` | Staff | Fila de trabalho por departamento |
| `pesquisa` | `/pedidos/staff/pesquisa/` | `pedidos:pesquisa` | Secretaria/Admin | Pesquisar pedidos com filtros |
| `pedido_staff_detalhe` | `/pedidos/staff/<pk>/` | `pedidos:pedido_staff_detalhe` | Staff | Detalhe do pedido com acções de staff |
| `aprovar` | `/pedidos/staff/<pk>/aprovar/` | `pedidos:aprovar` | Staff | Aprovar etapa do pedido |
| `indeferir` | `/pedidos/staff/<pk>/indeferir/` | `pedidos:indeferir` | Staff | Indeferir pedido |
| `marcar_pronto` | `/pedidos/staff/<pk>/marcar-pronto/` | `pedidos:marcar_pronto` | Secretaria/Admin | Marcar pedido como pronto |
| `marcar_entregue` | `/pedidos/staff/<pk>/marcar-entregue/` | `pedidos:marcar_entregue` | Staff | Registar entrega física |
| `carregar_extracto` | `/pedidos/staff/<pk>/carregar-extracto/` | `pedidos:carregar_extracto` | Crédito/Admin | Carregar extracto bancário |
| `painel` | `/painel/` | `painel` | Secretaria/Admin | Painel de indicadores com gráficos |

### Global (`config/urls.py`)

| URL | View | Nome |
| --- | --- | --- |
| `/admin/` | `admin.site.urls` | Admin Django |
| `/accounts/` | `allauth.urls` | Login social Google |
| `/contas/` | `contas.urls` | Contas próprias |
| `/painel/` | `pedidos.views.painel` | `painel` |
| `/pedidos/` | `pedidos.urls` | App pedidos |
| `/` | `contas.views.dashboard_redirect` | `home` |

## 9. Serviços e lógica de negócio

| Componente | Ficheiro | Funções principais | Descrição |
| --- | --- | --- | --- |
| Serviços de decisão | `pedidos/services.py` | `aprovar`, `indeferir`, `marcar_pronto`, `marcar_entregue`, `pode_decidir` | Regras de transição de etapas, bloqueio `select_for_update`, registo de decisões |
| Notificações | `pedidos/notificacoes.py` | `notificar_estudante` | Email ao estudante (pronto / indeferido), falha silenciosa no log |
| Validação de anexos | `pedidos/validators.py` | `validar_anexo` | Extensão, tamanho, assinatura binária (PDF/JPG/PNG) |
| Limite de login | `contas/views.py` | `LoginViewComLimite`, `_login_bloqueado`, `_incrementar_faltas` | Throttling por username e IP |
| Adapter social | `contas/adapters.py` | `ContasSocialAccountAdapter` | Valida domínio institucional no Google |

## 10. Comandos de gestão

| Comando | Ficheiro | Descrição |
| --- | --- | --- |
| `carregar_cursos` | `contas/management/commands/carregar_cursos.py` | Carrega catálogo de cursos (idempotente) |
| `importar_utilizadores` | `contas/management/commands/importar_utilizadores.py` | Importa utilizadores por CSV |
| `fazer_backup` | `pedidos/management/commands/fazer_backup.py` | Backup consistente SQLite + media/ em ZIP |
| `seed_demo` | `pedidos/management/commands/seed_demo.py` | Cria tipos de documento, utilizadores demo e pedidos de exemplo |

## 11. Testes

| Ficheiro | App | Descrição |
| --- | --- | --- |
| `contas/tests.py` | contas | Testes de perfis, importação, decoradores, signals |
| `contas/test_fase4.py` | contas | Testes de throttling de login (3 testes) |
| `contas/test_urls.py` | contas | URLs auxiliares para testes de decoradores |
| `pedidos/tests.py` | pedidos | Testes de tipos, seed, pedidos, anexos, staff |
| `pedidos/test_fase3.py` | pedidos | Testes da fase 3 (filas, decisões, entrega) |
| `pedidos/test_fase4.py` | pedidos | Testes da fase 4 (painel, backup, paginação, erros) |

## 12. Templates

| Template | Ficheiro | Uso |
| --- | --- | --- |
| Base | `templates/base.html` | Layout comum (topbar UCM, navegação por papel, mensagens) |
| Início | `templates/contas/home.html` | Dashboard por papel com contagens da fila |
| Login | `templates/contas/login.html` | Login clássico + Google (quando configurado) |
| Completar perfil | `templates/contas/completar_perfil.html` | Escolha de curso para estudante |
| Bloqueio número | `templates/contas/bloqueio_numero.html` | Quando não se identifica número de estudante |
| Novo pedido | `templates/pedidos/novo_pedido.html` | Formulário de submissão com HTMX + resumo |
| Resumo pedido | `templates/pedidos/_resumo_pedido.html` | Componente: taxa base, IVA, total, prazo |
| Meus pedidos | `templates/pedidos/meus_pedidos.html` | Lista paginada de pedidos do estudante |
| Detalhe pedido | `templates/pedidos/pedido_detalhe.html` | Detalhe do pedido para o estudante |
| Fila | `templates/pedidos/fila.html` | Fila de trabalho por departamento |
| Pesquisa | `templates/pedidos/pesquisa.html` | Pesquisa com filtros (secretaria/admin) |
| Detalhe staff | `templates/pedidos/pedido_staff_detalhe.html` | Detalhe + acções de staff |
| Painel | `templates/pedidos/painel.html` | Indicadores + gráficos Chart.js |
| Página 403 | `templates/403.html` | Acesso negado (tema UCM) |
| Página 404 | `templates/404.html` | Não encontrada (tema UCM) |
| Página 500 | `templates/500.html` | Erro interno (tema UCM) |
| Paginação | `templates/_paginacao.html` | Componente de paginação |

## 13. Ficheiros estáticos

- `static/css/input.css` — CSS de entrada do Tailwind (tokens de marca UCM, neutros slate,
  cores semânticas por estado, camadas base/componentes/utilitários)
- `static/css/app.css` — CSS compilado (Tailwind v4, minificado), gerado a partir de
  `input.css` via `tailwind.config.js`; referenciado em `templates/base.html`
- `static/css/ucm-theme.css` — Tema visual UCM-FEG (mantido, não referenciado por `base.html`)
- `static/img/logo-ucm.png` — Logótipo UCM
- `static/fonts/` — Fonte Inter local (4 variantes .woff2), declarada via `@font-face`
- `static/vendor/unpoly/unpoly.min.js` — Unpoly (interacção parcial, substitui HTMX)
- `static/vendor/unpoly/unpoly.min.css` — Estilos base do Unpoly
- `static/vendor/bootstrap/` — Bootstrap 5 (ficheiros físicos mantidos, NÃO referenciados)
- `static/vendor/bootstrap-icons/` — Bootstrap Icons (mantido, NÃO referenciado)
- `static/vendor/chartjs/chart.umd.min.js` — Chart.js para gráficos do painel (não alvo da migração)
- `static/tailwindcss` — Binário Tailwind CLI (não rastreado no Git)

## 14. Configuração de segurança (`config/settings.py`)

- `X_FRAME_OPTIONS = "DENY"` (linha 48)
- `SECURE_CONTENT_TYPE_NOSNIFF = True` (linha 49)
- `SECURE_REFERRER_POLICY = "same-origin"` (linha 50)
- `SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"` (linha 51)
- HSTS configurável por env (`DJANGO_HSTS_SECONDS`, etc.) (linhas 52-59)
- Cookies de sessão e CSRF seguros quando `DEBUG=False` (linhas 61-65)
- `SECURE_SSL_REDIRECT` configurável (linha 65)
- `CSRF_TRUSTED_ORIGINS` a partir de env (linhas 39-43)

## 15. Resumo dos fluxos implementados (deduzido do código)

1. **Login**: clássico (`LoginViewComLimite`) com throttling por username (5 falhas) e IP (20 falhas) numa janela de 15 min; Google institucional com validação de domínio no servidor (`ContasSocialAccountAdapter`).
2. **Perfil**: estudante deve completar curso (fixa o grau) e tem número de estudante extraído do email; middleware obriga a completar antes de aceder a outras páginas.
3. **Submissão**: estudante preenche tipo, motivo e anexos (BI + comprovativo); o resumo da taxa é
   actualizado via Unpoly (`up-target="#resumo-pedido"` + `up-autosubmit` no select de tipo);
   valor congelado em `Pedido.valor_total`.
4. **Tratamento**: secretaria aprova/indefer → crédito valida pagamento → registo valida percurso académico (se aplicável) → secretaria final marca pronto → entrega física.
5. **Decisões**: imutáveis (`Decisao.save`/`delete` levantam `DecisaoImutavelError`), com justificação, autor e data/hora.
6. **Notificações**: email ao estudante quando pronto ou indeferido; falha de envio registada no log sem reverter a decisão.
7. **Painel**: indicadores agregados, gráficos Chart.js via `json_script`, filtro por período, sem dados pessoais de estudantes.
8. **Backup**: comando `fazer_backup` cria ZIP consistente com SQLite (`Connection.backup`) + media/.

---

*Fim da varredura. Todos os factos acima são extraídos dos ficheiros reais do projecto.*