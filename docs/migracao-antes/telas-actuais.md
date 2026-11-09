# Telas actuais (estado ANTES da migração Fase 1)

Lista de telas e templates do projecto **Pedidos de Documentos · UCM-FEG**
antes de iniciar a migração para Tailwind + Unpoly.

## Templates (17 ficheiros)

### Base e layout
1. `templates/base.html` — Layout base com topbar UCM, navbar por perfil, Bootstrap CSS/JS

### Páginas públicas / autenticação
2. `templates/contas/login.html` — Login clássico + botão Google institucional
3. `templates/403.html` — Acesso negado (tema UCM)
4. `templates/404.html` — Página não encontrada (tema UCM)
5. `templates/500.html` — Erro interno (tema UCM)

### Contas (utilizador autenticado)
6. `templates/contas/home.html` — Página inicial por perfil (dashboard com stat tiles)
7. `templates/contas/completar_perfil.html` — Completar perfil académico (curso)
8. `templates/contas/bloqueio_numero.html` — Bloqueio quando não há número de estudante

### Pedidos (estudante)
9. `templates/pedidos/novo_pedido.html` — Novo pedido (formulário + resumo via HTMX)
10. `templates/pedidos/_resumo_pedido.html` — Partial: resumo da taxa
11. `templates/pedidos/meus_pedidos.html` — Meus pedidos (lista paginada)
12. `templates/pedidos/pedido_detalhe.html` — Detalhe do pedido (estudante)

### Pedidos (staff)
13. `templates/pedidos/fila.html` — Fila de trabalho por departamento
14. `templates/pedidos/pedido_staff_detalhe.html` — Detalhe staff com acções
15. `templates/pedidos/pesquisa.html` — Pesquisa de pedidos com filtros
16. `templates/pedidos/painel.html` — Painel de indicadores com gráficos

### Componentes
17. `templates/_paginacao.html` — Partial de paginação

## Bibliotecas estáticas actuais
- Bootstrap 5 CSS/JS (`static/vendor/bootstrap/`)
- Bootstrap Icons (`static/vendor/bootstrap-icons/`)
- HTMX (`static/vendor/htmx/htmx.min.js`)
- Chart.js (`static/vendor/chartjs/chart.umd.min.js`)
- CSS próprio: `static/css/ucm-theme.css` (46 linhas)

## Estado visual actual
- Topbar roxa escura (`#2d2a8c`) + barra de navegação escura (`#343a40`)
- Faixa de título (`ucm-page-header`) com fundo roxo e tira escura de 28px
- Títulos duplicados (topbar + página)
- Cartões sem raio, borda cinzenta clara, sem sombra
- Cores: roxo UCM como primário, azul (`#3b8de0`) como acção
- Bootstrap classes em todos os templates
