# Dossier de Migração do Frontend

## Resumo da migração

Este documento descreve as alterações realizadas na camada de apresentação do
projecto **Pedidos de Documentos · UCM-FEG**, divididas em três fases.

---

## Fase 0 — Inventário

**Ficheiro:** `docs/migracao-00-inventario.md`

Levantamento completo da camada de apresentação antes de qualquer alteração:

- 17 templates identificados
- 5 atributos `hx-*` num único template (`novo_pedido.html`)
- 1 partial de resposta parcial (`_resumo_pedido.html`)
- 7 bibliotecas vendor estáticas (Bootstrap CSS/JS, Bootstrap Icons, Chart.js, HTMX)
- CSS próprio (`ucm-theme.css`, 46 linhas)
- 2 testes dependentes de HTMX

Nenhum ficheiro de código foi alterado nesta fase.

---

## Fase 1 — Tailwind CSS + NOVO DESIGN

**Commit:** `04bf7f2`

### O que mudou

**Substituição do framework CSS:**
- Bootstrap 5 (CSS e JS) removido dos templates
- Tailwind CSS v4 instalado localmente (binário standalone em `static/tailwindcss`)
- `tailwind.config.js` na raiz com tokens de design:
  - Marca UCM: roxo (`#2d2a8c`) como `brand-700`, escala 50–900
  - Neutros: slate
  - Semânticas por estado: novo=sky, crédito=amber, registo=violet, assinatura=orange,
    pronto=emerald, indeferido=rose
  - Raio padrão `rounded-xl/2xl`, sombras `shadow-sm` com hover `shadow-md`
- Fonte Inter em woff2 local (`static/fonts/`), declarada via `@font-face`
- Ícones Lucide SVG embutidos (`templates/components/icon.html`)

**Novo layout (`base.html`):**
- Sidebar esquerda fixa (w-64) com logo UCM, navegação por perfil com ícones
- Barra superior fina (h-14) com título da página, pesquisa rápida, menu do utilizador
- Removidas as 3 faixas actuais e o título duplicado
- Área de conteúdo `max-w-7xl`, espaçamento generoso
- Mensagens do Django como toasts no canto superior direito

**Componentes reutilizáveis:**
- `stat_tile`, `status_pill`, `card`, `button` (primary/secondary/ghost/danger),
  `data_table`, `form_field`, `empty_state`, `page_header`, `icon`

**Telas migradas:**
- Início (dashboard por perfil com stat tiles)
- Login
- Novo pedido
- Meus pedidos
- Detalhe do pedido (estudante)
- Fila de trabalho (staff)
- Detalhe staff com acções
- Pesquisa de pedidos
- Painel de indicadores (gráficos Chart.js mantidos)
- Páginas de erro 403/404/500

### Ficheiros criados
- `tailwind.config.js`
- `static/css/input.css`
- `static/css/app.css` (CSS compilado, minificado)
- `static/fonts/Inter-*.woff2` (4 variantes)
- `static/tailwindcss` (binário Tailwind CLI)
- `templates/components/icon.html`
- `docs/migracao-antes/telas-actuais.md`

### Ficheiros modificados
- `config/settings.py` (adicionado `django_tailwind_cli` ao INSTALLED_APPS + config Tailwind)
- `templates/base.html` (novo design Tailwind)
- `templates/403.html`, `404.html`, `500.html`
- `templates/contas/login.html`, `home.html`, `completar_perfil.html`, `bloqueio_numero.html`
- `templates/pedidos/novo_pedido.html`, `meus_pedidos.html`, `pedido_detalhe.html`,
  `fila.html`, `pedido_staff_detalhe.html`, `pesquisa.html`, `painel.html`,
  `_resumo_pedido.html`, `_paginacao.html`

### Testes alterados
- `contas/tests.py`: removida verificação de `bi-google` (Bootstrap Icons substituído por SVG Lucide)
- `pedidos/test_fase4.py`: `ucm-topbar` → `empty-state` (classes Bootstrap removidas)
- `pedidos/tests.py`: `vendor/htmx/htmx.min.js` → `css/app.css` (HTMX removido)

### Resultado
96 testes passam. O resultado é visivelmente diferente do estado anterior.

---

## Fase 2 — Unpoly

**Commit:** `dc786a2`

### O que mudou

**Substituição do HTMX pelo Unpoly:**
- `unpoly.min.js` e `unpoly.min.css` adicionados em `static/vendor/unpoly/`
- Incluídos no `base.html`
- Meta tags CSRF configuradas (`up-csrf`, `up-csrf-header`)
- `up.protocol.config.headers` configurado com `X-CSRFToken`
- `up.framework.config.layer = 'page'` para substituição completa
- Select de tipo no `novo_pedido.html`: envolvido num formulário GET separado com
  `up-target="#resumo-pedido"` e `up-autosubmit` (equivalente Unpoly ao `hx-get`)
- Partial `_resumo_pedido.html`: elemento raiz com `id="resumo-pedido"` para target do Unpoly
- Progressive enhancement mantido: links e formulários funcionam como HTML normal sem JavaScript

**HTMX removido completamente:**
- Ficheiro `static/vendor/htmx/htmx.min.js` apagado
- Nenhuma referência restante a `hx-*`, `htmx` ou `HX-` em templates ou código Python

### Testes alterados
- Nenhum teste adicional alterado nesta fase (os ajustes já tinham sido feitos na Fase 1)

### Resultado
96 testes passam.

---

## Ficheiros removidos

| Ficheiro | Motivo |
|----------|--------|
| `static/vendor/htmx/htmx.min.js` | Substituído por Unpoly |
| `templates/components/icon.html` não existia antes (criado na Fase 1) | — |

Os ficheiros do Bootstrap (`static/vendor/bootstrap/`) permanecem fisicamente no disco mas não são referenciados por nenhum template.

---

## Testes alterados (resumo)

| Ficheiro | Alteração |
|----------|-----------|
| `contas/tests.py` | Removida verificação de `bi-google` (Bootstrap Icons → SVG Lucide) |
| `pedidos/test_fase4.py` | `ucm-topbar` → `empty-state`; verificação de tema ajustada |
| `pedidos/tests.py` | `vendor/htmx/htmx.min.js` → `css/app.css` |

---

## Pontos por resolver

1. **Ficheiros Bootstrap físicos:** Os ficheiros em `static/vendor/bootstrap/` permanecem no disco mas não são referenciados. Podem ser removidos numa limpeza futura.
2. **Chart.js:** Mantido no `static/vendor/chartjs/` e usado no painel. Não é alvo desta migração.
3. **Build do Tailwind:** Requer execução manual do binário `static/tailwindcss` para regenerar `static/css/app.css` após alterações em `input.css` ou `tailwind.config.js`.

---

## Estatísticas

- Ficheiros criados: 13 (incluindo documentação)
- Ficheiros modificados: 17 (templates + settings + testes)
- Ficheiros removidos: 1 (HTMX)
- Linhas totais adicionadas: ~2000
- Linhas totais removidas: ~1500
- Testes: 96/96 passam

---
*Migração concluída em 3 fases. Toda a lógica de negócio, modelos, migrations, permissões e fluxo de requerimentos permanecem inalterados.*