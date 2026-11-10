# 09. Interface — secção 5.4

## 9.1 Componentes de UI

| Componente | Ficheiro | Descrição |
| --- | --- | --- |
| Layout base | `templates/base.html` | HTML5, sidebar fixa (drawer mobile com `data-sidebar-toggle`/overlay), barra superior `h-14`, toasts do Django, meta CSRF para Unpoly, Tailwind CSS |
| Tema CSS / tokens de design | `static/css/app.css` + `static/css/input.css` + `tailwind.config.js` | Tailwind CSS v4 compilado: marca UCM (`brand-700` `#2d2a8c`, escala 50–900), neutros slate, cores semânticas por estado (novo=sky, crédito=amber, registo=violet, assinatura=orange, pronto=emerald, indeferido=rose), fonte Inter, raios e sombras |
| Ícones | `templates/components/icon.html` | Ícones Lucide SVG embutidos localmente (uso: `{% include "components/icon.html" with icon_name="..." %}`) |
| JS interatividade | `static/vendor/unpoly/unpoly.min.js` | Unpoly (substitui HTMX): `up-target="#resumo-pedido"` + `up-autosubmit` no select de tipo do novo pedido; CSRF via meta tags `up-csrf`/`up-csrf-header` e cabeçalho `X-CSRFToken` |
| Gráficos | `static/vendor/chartjs/chart.umd.min.js` | Chart.js para gráficos do painel (não alvo da migração) |
| Logótipo | `static/img/logo-ucm.png` | Logótipo UCM na sidebar e topbar |
| Tabela com scroll | `templates/components/table_wrap.html` (+ `table_wrap_open/close`) | Wrapper `overflow-x-auto` para tabelas em ecrãs pequenos |
| Componente paginação | `templates/_paginacao.html` | Paginação de 25 itens reutilizável |

O design é responsivo com utilitários Tailwind (`lg:`, `md:`, `sm:`): sidebar fixa em
desktop e drawer (oculta com `-translate-x-full`) em mobile; tabelas com scroll
horizontal (`overflow-x-auto`) em ecrãs pequenos.

**Ficheiro:** `templates/base.html`.

## 9.2 Tokens de design (cores por estado)

| Token | Valor | Uso |
| --- | --- | --- |
| `brand-50 … brand-900` | `#f5f3ff … #161353` (roxo UCM, `brand-700 = #2d2a8c`) | Marca principal, botões primários, estado activo |
| `slate-50 … slate-900` | `#f8fafc … #0f172a` | Fundo, textos, bordas neutros |
| `estado-novo` | `#0ea5e9` (sky) | Pedido recém-criado / em tratamento |
| `estado-credito` | `#f59e0b` (amber) | Etapa controlo de crédito |
| `estado-registo` | `#8b5cf6` (violet) | Etapa registo académico |
| `estado-assinatura` | `#f97316` (orange) | Etapa assinatura da direcção |
| `estado-pronto` | `#10b981` (emerald) | Pedido pronto para levantamento |
| `estado-indeferido` | `#f43f5e` (rose) | Pedido indeferido |

Fonte: `tailwind.config.js` e `static/css/input.css` (`@theme`).

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
| `pedidos/novo_pedido.html` | `/pedidos/novo/` | Formulário: tipo, motivo, 2 anexos; resumo da taxa actualizado via Unpoly (`up-autosubmit`) | Submeter pedido |
| `pedidos/_resumo_pedido.html` | (include) | Taxa base, IVA, total a pagar, prazo estimado; alvo Unpoly `id="resumo-pedido"` | — |
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

Todas usam o tema visual UCM-FEG (Tailwind, cores da marca) e não revelam
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

## 9.5 Capturas de ecrã (ligação a `docs/screens/`)

As capturas seguintes já existem em `docs/screens/` (geradas pelo teste
Playwright `test_mobile_playwright.py`, commit `438d4de`):

| Ficheiro | Largura | O que mostra |
| --- | --- | --- |
| `desktop_1440_inicial.png` | 1440px | Página de fila em desktop; sidebar visível à esquerda |
| `desktop_1440_completa.png` | 1440px | Página completa em desktop |
| `mobile_390_inicial.png` | 390px | Página de fila em mobile; sidebar fechada (esquerda negativa) |
| `mobile_390_apos_clique.png` | 390px | Página em mobile após clicar no botão hambúrguer; sidebar aberta |
| `mobile_390_completa.png` | 390px | Página completa em mobile |

**Capturas em falta (não existem em `docs/screens/`):**
- Login (`/contas/login/`)
- Página inicial por perfil (`/`) para cada papel (estudante, secretaria, crédito, registo, admin)
- Novo pedido (`/pedidos/novo/`) com resumo da taxa
- Meus pedidos (`/pedidos/meus/`)
- Detalhe do pedido (`/pedidos/<pk>/`)
- Fila de trabalho (`/pedidos/staff/fila/`) por cada papel staff
- Detalhe staff (`/pedidos/staff/<pk>/`)
- Pesquisa (`/pedidos/staff/pesquisa/`)
- Painel (`/painel/`)
- Páginas de erro 403/404/500

---
*Todos os factos são extraídos do código real do projecto.*