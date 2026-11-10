# 15. Evolução do projecto

Cronologia a partir do histórico de commits (`git log --oneline`) e do
`docs/migracao-resumo.md`. Só factos sustentados pelo histórico; nenhuma fase
inventada.

## Fase A — Projecto base e funcionalidades de backend (pré-migração do frontend)

| Commit | Mensagem | O que mudou |
|--------|----------|-------------|
| `8d03ad4` | projecto base | Base do Django com configuração, apps `contas` e `pedidos`, modelos, URLs. |
| `c2d8e6b` | fase 1: perfis, login institucional e tipos de documento | Perfis com papéis, login clássico com limite de tentativas, login Google institucional (django-allauth), tipos de documento com taxas. |
| `f6c3b84` | fase 2: pedido do estudante, anexos protegidos e acompanhamento | Submissão de pedidos com anexos (BI + comprovativo), validação de anexos, detalhe do pedido, descarga protegida de anexos. |
| `2e16035` | fase 3: filas, decisões, entrega e emails | Fila de trabalho por departamento, serviços de decisão (aprovar/indeferir/pronto/entregue), decisões imutáveis, notificações por email. |
| `48edc38` | fase 3b: número de estudante pelo email e curso por lista | Número de estudante extraído do email, catálogo de cursos. |
| `0c59ec6` | tarefa 5: dados dos cursos e comando carregar_cursos | Comando `carregar_cursos` idempotente. |
| `b1bb672` | fase 4: painel, backups e endurecimento | Painel de indicadores com gráficos (Chart.js), comando `fazer_backup`, paginação, páginas de erro temáticas, verificações de segurança. |
| `703ee84` | remover taxa do formulário (só aplicável ao pedido físico) | Valor do pedido passa a ser só taxa do tipo + IVA (taxa de formulário removida). |
| `d2731c0` | added markdown docs for about the whole project | Criação do dossier técnico `docs/00` a `docs/14` (gerado **antes** da migração do frontend). |

## Fase B — Migração do frontend (Bootstrap/HTMX → Tailwind/Unpoly)

Sustentada por `docs/migracao-resumo.md` e pelos commits `2126283`, `ee81d56`,
`10b04c6`.

### Fase B.1 — Tailwind CSS + novo design

**Commit:** `2126283` "fase 1: substituir Bootstrap/HTMX por Tailwind CSS com novo design"

O que mudou:
- Bootstrap 5 (CSS e JS) removido dos templates (ficheiros físicos mantidos em
  `static/vendor/bootstrap/`, mas não referenciados).
- Tailwind CSS v4 instalado localmente; `static/css/input.css` (tokens e
  camadas) compilado para `static/css/app.css` via `tailwind.config.js`.
- `tailwind.config.js` na raiz com tokens da marca UCM (roxo `brand-700`
  `#2d2a8c`, escala 50–900), neutros slate, cores semânticas por estado do
  requerimento (novo=sky, crédito=amber, registo=violet, assinatura=orange,
  pronto=emerald, indeferido=rose).
- Fonte Inter local (`static/fonts/*.woff2`) via `@font-face`.
- Ícones Lucide SVG embutidos em `templates/components/icon.html`.
- Novo `base.html`: sidebar esquerda fixa, barra superior (`h-14`), área de
  conteúdo `max-w-7xl`, toasts do Django.
- Componentes reutilizáveis: `card`, `button` (primary/secondary/ghost/danger),
  `data_table`, `form_field`, `empty_state`, `page_header`, `stat_tile`,
  `status_pill`, `icon`.
- Todas as telas migradas para Tailwind (início, login, novo pedido, meus
  pedidos, detalhe, fila, pesquisa, painel, erros 403/404/500).
- Testes adaptados (removida referência a `bi-google`, `ucm-topbar`,
  `vendor/htmx`).

### Fase B.2 — Unpoly substitui HTMX

**Commit:** `ee81d56` "fase 2: substituir HTMX por Unpoly"

O que mudou:
- `unpoly.min.js` e `unpoly.min.css` adicionados em `static/vendor/unpoly/`
  e incluídos em `base.html`.
- Meta tags CSRF configuradas (`up-csrf`, `up-csrf-header`) e
  `up.protocol.config.headers` com `X-CSRFToken`; `up.framework.config.layer =
  'page'`.
- Select de tipo em `novo_pedido.html` envolto num formulário GET separado com
  `up-target="#resumo-pedido"` e `up-autosubmit` (equivalente Unpoly ao `hx-get`).
- Partial `_resumo_pedido.html` com elemento raiz `id="resumo-pedido"`.
- HTMX removido completamente: ficheiro `static/vendor/htmx/htmx.min.js`
  apagado; nenhuma referência a `hx-*`/`htmx`/`HX-` em templates nem Python.

### Fase B.3 — README e resumo da migração

**Commit:** `10b04c6` "fase 3: atualizar README e resumo da migração"

O que mudou:
- `README.md` actualizado com a secção "Compilar o CSS (Tailwind)".
- Criação de `docs/migracao-resumo.md` (inventário da migração em 3 fases).

## Fase C — Correcções e limpeza pós-migração

| Commit | Mensagem | O que mudou |
|--------|----------|-------------|
| `438d4de` | corrigir sidebar mobile e scroll das tabelas | Sidebar mobile (drawer, botão hambúrguer, overlay, tecla Esc), tabelas com scroll horizontal (`table_wrap`), capturas de ecrã em `docs/screens/` (desktop 1440px e mobile 390px). |
| `94b8cfb` | remover executável do Tailwind CLI do rastreamento do Git | `static/tailwindcss` deixado de ser rastreado no Git (`.gitignore`). |

## Porquê da migração (sustentado pelo histórico e por `docs/migracao-resumo.md`)

- Substituir Bootstrap 5 + HTMX por Tailwind CSS v4 + Unpoly, mantendo toda a
  lógica de negócio, modelos, migrations, permissões e fluxo de requerimentos
  inalterados.
- Obter um novo design (sidebar fixa + topbar, tokens de marca UCM, fonte Inter,
  ícones Lucide), componentes reutilizáveis e correcções mobile (sidebar, tabelas
  com scroll).
- Servir todos os activos de frontend localmente (sem CDN): CSS compilado,
  fontes locais, ícones SVG, Unpoly local.
- Manter o número de testes a passar (96/96) ao longo da migração.

## Estado actual do frontend (resultado da migração)

- CSS: `static/css/app.css` (Tailwind v4, compilado de `static/css/input.css`).
- Interactividade parcial: Unpoly (só no select de tipo do novo pedido; resto
  é HTML progressivo).
- Gráficos do painel: Chart.js mantido (não alvo da migração).
- Bootstrap/Bootstrap Icons: ficheiros físicos em disco, não referenciados.
- HTMX: removido completamente.
