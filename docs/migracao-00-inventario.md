# 00. Inventário — Migração do Frontend (Fase 0)

Este documento lista tudo o que existe actualmente na camada de apresentação
do projecto **Pedidos de Documentos · UCM-FEG**, antes de qualquer alteração.
Não se altera nenhum ficheiro de código nesta fase.

---

## 1. Templates (17 ficheiros)

| # | Caminho | Descrição |
|---|---------|-----------|
| 1 | `templates/base.html` | Layout base: topbar UCM, navbar por perfil, mensagens Django, Bootstrap CSS/JS |
| 2 | `templates/contas/home.html` | Página inicial por perfil (estudante, secretaria, crédito, registo, admin) |
| 3 | `templates/contas/login.html` | Login clássico + botão Google institucional |
| 4 | `templates/contas/completar_perfil.html` | Formulário de completar perfil académico (curso) |
| 5 | `templates/contas/bloqueio_numero.html` | Página de bloqueio quando não há número de estudante |
| 6 | `templates/pedidos/novo_pedido.html` | Formulário de novo pedido (tipo, motivo, 2 anexos) + **HTMX** para resumo da taxa |
| 7 | `templates/pedidos/_resumo_pedido.html` | **Partial**: resumo da taxa (base, IVA, total, prazo) — resposta parcial via HTMX |
| 8 | `templates/pedidos/meus_pedidos.html` | Lista paginada de pedidos do estudante |
| 9 | `templates/pedidos/pedido_detalhe.html` | Detalhe do pedido para o estudante (estado, anexos, valor) |
| 10 | `templates/pedidos/fila.html` | Fila de trabalho por departamento (staff) |
| 11 | `templates/pedidos/pedido_staff_detalhe.html` | Detalhe staff com acções (aprovar, indeferir, pronto, entregue, extracto) |
| 12 | `templates/pedidos/pesquisa.html` | Pesquisa de pedidos com filtros (secretaria/admin) |
| 13 | `templates/pedidos/painel.html` | Painel de indicadores com **Chart.js** |
| 14 | `templates/403.html` | Acesso negado (tema UCM) |
| 15 | `templates/404.html` | Página não encontrada (tema UCM) |
| 16 | `templates/500.html` | Erro interno (tema UCM) |
| 17 | `templates/_paginacao.html` | **Partial**: componente de paginação reutilizável |

---

## 2. Usos de `hx-*` e cabeçalhos `HX-*`

### Templates com atributos `hx-*`

Apenas **um template** usa HTMX:

| Ficheiro | Linha | Atributo | Valor | Propósito |
|----------|-------|----------|-------|-----------|
| `templates/pedidos/novo_pedido.html` | 55 | `hx-get` | `{% url 'pedidos:resumo_pedido' %}` | Buscar resumo da taxa |
| `templates/pedidos/novo_pedido.html` | 56 | `hx-trigger` | `change` | Disparar ao mudar o select de tipo |
| `templates/pedidos/novo_pedido.html` | 57 | `hx-target` | `#resumo-pedido` | Substituir o elemento resumo |
| `templates/pedidos/novo_pedido.html` | 58 | `hx-swap` | `outerHTML` | Trocar todo o elemento alvo |
| `templates/pedidos/novo_pedido.html` | 59 | `hx-include` | `[name='tipo']` | Enviar apenas o campo tipo |

O atributo está no `<select name="tipo">` (linha 51-59).

### Script HTMX no template

| Ficheiro | Linha | Código |
|----------|-------|--------|
| `templates/pedidos/novo_pedido.html` | 129 | `<script src="{% static 'vendor/htmx/htmx.min.js' %}"></script>` |

Está no bloco `extra_js`.

### Views relacionadas com HTMX

| Ficheiro | Linha | Função/View | Observação |
|----------|-------|-------------|------------|
| `pedidos/views.py` | 154 | `resumo_pedido` | Devolve `pedidos/_resumo_pedido.html` como resposta parcial |
| `pedidos/views.py` | 60 | `_contexto_resumo` | Contexto compartilhado (tipo, taxa_base, iva, total, prazo, grau) |

**Não existem verificações de `request.htmx`** em nenhuma view.

### Testes que dependem de HTMX

| Ficheiro | Linha | Código | O que testa |
|----------|-------|--------|-------------|
| `pedidos/tests.py` | 327 | `self.assertContains(resposta, 'vendor/htmx/htmx.min.js') | Que o script HTMX está presente na página de novo pedido |
| `pedidos/tests.py` | 478 | `test_endpoint_htmx_devolve_a_taxa_certa_para_cada_grau` | Endpoint `resumo_pedido` devolve taxa correcta por grau (nome menciona HTMX, mas testa a lógica do endpoint) |

---

## 3. Partials usados como resposta parcial

| Partial | Usado por | View que o devolve |
|---------|-----------|-------------------|
| `templates/pedidos/_resumo_pedido.html` | `novo_pedido.html` (via HTMX `hx-target="#resumo-pedido"`) | `pedidos.views.resumo_pedido` (linha 162) |
| `templates/_paginacao.html` | `fila.html`, `meus_pedidos.html`, `pesquisa.html` (via `{% include %}`) | Não é uma resposta parcial — é incluído no servidor |

---

## 4. Ficheiros estáticos (vendor + próprio)

### `static/vendor/` (bibliotecas de terceiros)

| Caminho | Tamanho aprox. | Uso |
|---------|----------------|-----|
| `static/vendor/bootstrap/css/bootstrap.min.css` | — | CSS framework (base do tema actual) |
| `static/vendor/bootstrap-icons/bootstrap-icons.min.css` | — | Ícones Bootstrap |
| `static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff` | — | Fonte de ícones |
| `static/vendor/bootstrap-icons/fonts/bootstrap-icons.woff2` | — | Fonte de ícones |
| `static/vendor/bootstrap/js/bootstrap.bundle.min.js` | — | JS do Bootstrap (dropdowns, etc.) |
| `static/vendor/chartjs/chart.umd.min.js` | — | Gráficos do painel (`painel.html` linha 220) |
| `static/vendor/htmx/htmx.min.js` | — | **HTMX** (apenas `novo_pedido.html` linha 129) |

### CSS próprio

| Caminho | Linhas | Descrição |
|---------|--------|-----------|
| `static/css/ucm-theme.css` | 46 | Sobrescritas do tema UCM: cores (roxo `#2d2a8c`, azul `#3b8de0`), botões, topbar, navbar, cartões sem raio |

### Imagens

| Caminho | Observação |
|---------|------------|
| `static/img/logo-ucm.png` | Logótipo UCM (usado em `base.html`) |
| `static/img/equipamentos_avarias_nova_(Nest Hub Max).png` | Não usado nos templates (parece ser de outro projecto) |
| `static/img/etiquetas_(Nest Hub Max).png` | Não usado nos templates |
| `static/img/ficha_equipamentos_1_(Nest Hub Max).png` | Não usado nos templates |
| `static/img/indicadores_equipamentos_dashboard_(Nest Hub Max).png` | Não usado nos templates |
| `static/img/lista_equipamentos_avarias_(Nest Hub Max).png` | Não usado nos templates |

---

## 5. Bibliotecas JS/CSS carregadas no `base.html`

| Recurso | Caminho | Carregado em |
|---------|---------|--------------|
| Bootstrap CSS | `{% static 'vendor/bootstrap/css/bootstrap.min.css' %}` | `base.html` linha 9 |
| Bootstrap Icons CSS | `{% static 'vendor/bootstrap-icons/bootstrap-icons.min.css' %}` | `base.html` linha 10 |
| UCM Theme CSS | `{% static 'css/ucm-theme.css' %}` | `base.html` linha 11 |
| Bootstrap JS Bundle | `{% static 'vendor/bootstrap/js/bootstrap.bundle.min.js' %}` | `base.html` linha 144 |
| HTMX JS | `{% static 'vendor/htmx/htmx.min.js' %}` | `novo_pedido.html` linha 129 (apenas nesta página) |
| Chart.js | `{% static 'vendor/chartjs/chart.umd.min.js' %}` | `painel.html` linha 220 (apenas nesta página) |

---

## 6. Dependências em `requirements.txt`

| Pacote | Versão | Relação com frontend |
|--------|--------|----------------------|
| Django | 6.1.3 | Framework |
| django-allauth | 65.21.1 | Autenticação (login social Google) |
| (nenhum) | — | **Não existe `django-htmx`, `django-tailwind`, `unpoly`, etc.** |

---

## 7. O que depende do CSS/JS do template antigo (Bootstrap)

Tudo o que usa classes Bootstrap nos templates:

| Ficheiro | Classes Bootstrap usadas |
|----------|-------------------------|
| `base.html` | `container`, `d-flex`, `btn`, `dropdown`, `navbar`, `nav-link`, `collapse`, `alert`, `btn-close`, `btn-primary`, `btn-outline-*`, `text-white`, `text-muted`, `fw-semibold`, `d-grid`, `gap-*`, `py-*`, `px-*`, `me-*`, `ms-*`, `mb-*`, `mt-*`, `w-100`, `d-block`, `d-none` (implícito) |
| `contas/home.html` | `card`, `card-body`, `card-title`, `card-text`, `badge`, `text-bg-*`, `btn`, `btn-primary`, `btn-outline-primary`, `w-100`, `mt-auto`, `col-*`, `row`, `g-4`, `dl`, `dt`, `dd`, `h2`, `h3`, `h4`, `h5`, `text-uppercase`, `text-muted`, `fw-semibold`, `flex-grow-1`, `d-flex`, `flex-column`, `justify-content-between` |
| `contas/login.html` | `card`, `card-body`, `btn`, `btn-outline-danger`, `btn-primary`, `w-100`, `alert`, `alert-danger`, `form-control`, `form-label`, `form-text`, `text-muted`, `text-center`, `mb-*`, `mt-*`, `col-*`, `row`, `g-*`, `shadow-sm`, `fs-1`, `h4`, `h6` |
| `contas/completar_perfil.html` | `card`, `card-body`, `card-title`, `card-text`, `form-control`, `form-select`, `form-label`, `invalid-feedback`, `d-block`, `btn`, `btn-primary`, `btn-outline-secondary`, `optgroup`, `col-*`, `row`, `g-*`, `mb-*`, `mt-*`, `text-danger`, `text-muted`, `small`, `form-text` |
| `contas/bloqueio_numero.html` | `card`, `card-body`, `card-title`, `border-danger`, `text-danger`, `btn`, `btn-outline-secondary`, `h2`, `h4`, `p`, `text-muted`, `strong` |
| `pedidos/novo_pedido.html` | `card`, `card-body`, `card-title`, `form-select`, `form-label`, `form-control`, `form-text`, `invalid-feedback`, `d-block`, `btn`, `btn-primary`, `btn-outline-secondary`, `alert`, `alert-info`, `text-muted`, `text-danger`, `fw-bold`, `small`, `col-*`, `row`, `g-4`, `mb-*`, `d-flex`, `gap-2`, `h2`, `h4`, `i` (bi-*) |
| `pedidos/_resumo_pedido.html` | `card`, `card-body`, `card-header`, `bg-primary`, `text-white`, `dl`, `row`, `dt`, `dd`, `col-*`, `text-end`, `fw-bold`, `form-text`, `mt-*`, `mb-*`, `text-muted` |
| `pedidos/meus_pedidos.html` | `card`, `card-body`, `table`, `table-hover`, `align-middle`, `bg-white`, `btn`, `btn-primary`, `btn-outline-primary`, `badge`, `text-bg-*`, `text-danger`, `text-success`, `text-secondary`, `text-muted`, `fw-semibold`, `col-*`, `row`, `g-*`, `mb-*`, `text-end`, `h2`, `h4`, `p`, `d-flex`, `justify-content-between`, `gap-2` |
| `pedidos/pedido_detalhe.html` | `card`, `card-body`, `card-header`, `badge`, `text-bg-*`, `dl`, `row`, `dt`, `dd`, `col-sm-*`, `alert`, `alert-danger`, `mt-*`, `mb-*`, `btn`, `btn-outline-primary`, `btn-outline-secondary`, `w-100`, `list-group`, `list-group-flush`, `list-group-item`, `d-flex`, `align-items-center`, `justify-content-between`, `gap-2`, `px-0`, `col-*`, `row`, `g-4` |
| `pedidos/fila.html` | `card`, `card-body`, `d-flex`, `flex-wrap`, `align-items-center`, `justify-content-between`, `gap-2`, `mb-*`, `h2`, `h4`, `btn`, `btn-outline-primary`, `btn-primary`, `w-100`, `form-select`, `form-label`, `nav`, `nav-tabs`, `nav-link`, `active`, `badge`, `text-bg-secondary`, `table`, `table-hover`, `align-middle`, `bg-white`, `btn`, `btn-sm`, `btn-outline-primary`, `col-*`, `row`, `g-2`, `text-end`, `small`, `text-muted` |
| `pedidos/pedido_staff_detalhe.html` | `card`, `card-body`, `card-header`, `badge`, `text-bg-primary`, `dl`, `row`, `dt`, `dd`, `col-sm-*`, `alert`, `alert-danger`, `mt-*`, `mb-*`, `btn`, `btn-outline-primary`, `btn-success`, `btn-primary`, `btn-outline-danger`, `w-100`, `mt-*`, `d-grid`, `gap-3`, `list-group`, `list-group-flush`, `list-group-item`, `px-0`, `d-flex`, `align-items-center`, `justify-content-between`, `gap-2`, `badge`, `text-bg-secondary`, `small`, `text-muted`, `fs-4`, `text-uppercase`, `col-*`, `row`, `g-3`, `g-4` |
| `pedidos/pesquisa.html` | `card`, `card-body`, `form-control`, `form-select`, `form-label`, `btn`, `btn-primary`, `btn-outline-secondary`, `w-100`, `btn-sm`, `table`, `table-hover`, `align-middle`, `bg-white`, `btn`, `btn-sm`, `btn-outline-primary`, `badge`, `text-bg-*`, `text-muted`, `fw-semibold`, `col-*`, `row`, `g-3`, `align-items-end`, `d-flex`, `flex-wrap`, `justify-content-between`, `gap-2`, `mb-*`, `h2`, `h4`, `p`, `display-4`, `text-center`, `py-5` |
| `pedidos/painel.html` | `card`, `card-body`, `card-header`, `bg-white`, `fw-semibold`, `table`, `table-hover`, `align-middle`, `mb-0`, `btn`, `btn-primary`, `form-select`, `form-label`, `badge`, `text-bg-*`, `text-muted`, `text-danger`, `text-success`, `text-secondary`, `fw-bold`, `small`, `col-*`, `row`, `g-3`, `mb-*`, `h2`, `h4`, `p`, `text-center`, `py-5`, `display-6`, `d-flex`, `flex-wrap`, `align-items-end`, `justify-content-between`, `gap-3`, `table-danger`, `canvas` |
| `403.html`, `404.html`, `500.html` | `card`, `card-body`, `text-center`, `p-5`, `btn`, `btn-primary`, `h1`, `h2`, `h4`, `p`, `text-muted`, `col-*`, `row`, `justify-content-center`, `py-4`, `i` (bi-*), `bi-shield-lock`, `bi-compass`, `bi-exclamation-triangle`, `bi-house-door` |

---

## 8. Resumo do que precisa de mudar

| Item | Actual | Alvo (Fase 1+2) |
|------|--------|-----------------|
| CSS framework | Bootstrap 5 (via `static/vendor/bootstrap/`) | Tailwind CSS (compilado localmente) |
| Ícones | Bootstrap Icons | Lucide SVG (local) |
| Interactividade parcial | HTMX | Unpoly |
| JS gráfico (painel) | Chart.js | Mantém (não é alvo da migração) |
| CSS próprio | `static/css/ucm-theme.css` | Substituído por `static/css/app.css` (Tailwind) |
| Fonte | Sistema (Bootstrap) | Inter woff2 local |

---

## 9. Testes que dependem da camada de apresentação actual

| Ficheiro | Linha | O que testa | Impacto da migração |
|----------|-------|-------------|---------------------|
| `pedidos/tests.py` | 327 | `vendor/htmx/htmx.min.js` presente | **Vai falhar** — HTMX será removido |
| `pedidos/tests.py` | 478 | Endpoint `resumo_pedido` | Mantém-se (endpoint continua a existir, mas muda a forma como é chamado) |

---

**Fim do inventário da Fase 0.** Nenhum ficheiro foi alterado. Aguardo confirmação para avançar para a Fase 1.