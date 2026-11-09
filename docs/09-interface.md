# 09. Interface — secção 5.4

## 9.1 Componentes de UI

| Componente | Ficheiro | Descrição |
| --- | --- | --- |
| Layout base | `templates/base.html` | HTML5, topbar UCM, navbar por papel, mensagens, Bootstrap 5 |
| Tema CSS | `static/css/ucm-theme.css` | Estilos visuais da UCM-FEG |
| Ícones | `static/vendor/bootstrap-icons/` | Bootstrap Icons (bi-*) |
| JS interatividade | `static/vendor/htmx/htmx.min.js` | HTMX para resumo da taxa sem recarregar página |
| Gráficos | `static/vendor/chartjs/chart.umd.min.js` | Chart.js para gráficos do painel |
| Logótipo | `static/img/logo-ucm.png` | Logótipo UCM na topbar |

O design é responsivo (classes Bootstrap `col-*`, `container`, `navbar-expand-lg`).

**Ficheiro:** `templates/base.html` (linhas 1-147).

## 9.2 Telas por perfil

### Visitante / não autenticado

| Template | URL | O que mostra | Acções |
| --- | --- | --- | --- |
| `contas/login.html` | `/contas/login/` | Formulário de login (username/password) + botão Google (se configurado) | Entrar, entrar com Google |
| `base.html` (home) | `/` | Redireccionado para login se não autenticado | — |

### Estudante

| Template | URL | O que mostra | Acções |
| --- | --- | --- | --- |
| `contas/home.html` | `/` | Área do estudante: Novo pedido, Meus pedidos, Dados académicos | Navegar para funcionalidades |
| `contas/completar_perfil.html` | `/contas/completar-perfil/` | Escolha de curso (agrupado por grau), telefone | Guardar perfil |
| `contas/bloqueio_numero.html` | (redireccionamento) | Mensagem: número de estudante não identificado; contactar Secretaria | Sair |
| `pedidos/novo_pedido.html` | `/pedidos/novo/` | Formulário: tipo, motivo, 2 anexos; resumo da taxa (HTMX) | Submeter pedido |
| `pedidos/_resumo_pedido.html` | (include) | Taxa base, IVA, total a pagar, prazo estimado | — |
| `pedidos/meus_pedidos.html` | `/pedidos/meus/` | Lista paginada (25) de pedidos com estado e etapa | Ver detalhe, novo pedido |
| `pedidos/pedido_detalhe.html` | `/pedidos/<pk>/` | Detalhe: tipo, grau, motivo, valor, etapa, anexos | Descarregar anexos |

### Secretaria

| Template | URL | O que mostra | Acções |
| --- | --- | --- | --- |
| `contas/home.html` | `/` | Área da Secretaria: contagens (novos, assinatura, prontos), Painel | Abrir fila, abrir painel |
| `pedidos/fila.html` | `/pedidos/staff/fila/` | Fila de novos e assinatura, com contagens | Abrir detalhe, pesquisa |
| `pedidos/pedido_staff_detalhe.html` | `/pedidos/staff/<pk>/` | Detalhe completo + acções: aprovar, indeferir, marcar pronto, marcar entregue | Decidir sobre o pedido |
| `pedidos/pesquisa.html` | `/pedidos/staff/pesquisa/` | Pesquisa com filtros (protocolo, nome, estado, etapa, tipo) | Abrir detalhe |
| `pedidos/painel.html` | `/painel/` | Indicadores, gráficos, tempo médio, pedidos antigos | Filtrar por período |

### Controlo de Crédito

| Template | URL | O que mostra | Acções |
| --- | --- | --- | --- |
| `contas/home.html` | `/` | Área de Crédito: contagem da fila do crédito | Abrir fila |
| `pedidos/fila.html` | `/pedidos/staff/fila/` | Fila de pedidos na etapa crédito | Abrir detalhe, carregar extracto |
| `pedidos/pedido_staff_detalhe.html` | `/pedidos/staff/<pk>/` | Detalhe + conferência de pagamento (valor esperado vs comprovativo) | Aprovar, indeferir, carregar extracto |

### Registo Académico

| Template | URL | O que mostra | Acções |
| --- | --- | --- | --- |
| `contas/home.html` | `/` | Área de Registo: contagem da fila do registo | Abrir fila |
| `pedidos/fila.html` | `/pedidos/staff/fila/` | Fila de pedidos na etapa registo | Abrir detalhe |
| `pedidos/pedido_staff_detalhe.html` | `/pedidos/staff/<pk>/` | Detalhe do pedido | Aprovar, indeferir |

### Administrador

| Template | URL | O que mostra | Acções |
| --- | --- | --- | --- |
| `contas/home.html` | `/` | Área de Admin: todas as contagens, Painel, Gestão do sistema, Contas e perfis | Abrir fila, painel, admin Django |
| `pedidos/fila.html` | `/pedidos/staff/fila/` | Fila com filtro por etapa | Abrir detalhe |
| `pedidos/pesquisa.html` | `/pedidos/staff/pesquisa/` | Pesquisa completa | Abrir detalhe |
| `pedidos/painel.html` | `/painel/` | Indicadores completos | Filtrar por período |
| Admin Django | `/admin/` | Gestão de utilizadores, perfis, cursos, tipos de documento, pedidos (só-leitura) | CRUD de dados de referência |

## 9.3 Páginas de erro

| Template | URL (implícita) | O que mostra | Link |
| --- | --- | --- | --- |
| `403.html` | Acesso negado (PermissionDenied) | "Não tem permissão para esta página" | Voltar à página inicial |
| `404.html` | Página não encontrada | "Não encontrámos esta página" | Voltar à página inicial |
| `500.html` | Erro interno | "Algo não correu como esperado" | Voltar à página inicial |

Todas usam o tema UCM (`ucm-topbar`, `ucm-page-header`) e não revelam
informação sensível.

**Ficheiro:** `templates/403.html`, `404.html`, `500.html`.

## 9.4 Decisões de design

- Tema visual consistente da UCM-FEG em todas as páginas (`base.html`).
- Navegação condicionada pelo papel do utilizador (estudante vê "Novo
  pedido"/"Meus pedidos"; staff vê "Fila"; secretaria/admin vê "Pesquisa" e
  "Painel").
- Páginas de erro temáticas com link para a página inicial, sem expor
  stack traces ao utilizador.
- Paginação de 25 itens em `meus_pedidos` e `fila`.
- Formulário de novo pedido mostra limites de anexo (tamanho e tipos
  aceites).

---
*Todos os factos são extraídos do código real do projecto.*