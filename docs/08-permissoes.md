# 08. Permissões — view/rota, URL, perfis e mecanismo

## 8.1 Tabela de permissões

| View / Rota | URL | Perfis permitidos | Mecanismo | Ficheiro / Linha |
| --- | --- | --- | --- | --- |
| Login (clássico) | `/contas/login/` | Público | Nenhuma (público) | `contas/views.py` `LoginViewComLimite`, linha 59 |
| Logout | `/contas/logout/` | Autenticado | `@login_required` (via allauth) | `contas/urls.py` linha 14 |
| Completar perfil | `/contas/completar-perfil/` | Estudante | Verificação de papel na view | `contas/views.py` `completar_perfil`, linha 165 |
| Página inicial | `/` | Autenticado | `@login_required` | `contas/views.py` `dashboard_redirect`, linha 148 |
| Novo pedido | `/pedidos/novo/` | Estudante | `@estudante_required` | `pedidos/views.py` `novo_pedido`, linha 91 |
| Meus pedidos | `/pedidos/meus/` | Estudante | `@estudante_required` | `pedidos/views.py` `meus_pedidos`, linha 166 |
| Resumo pedido (HTMX) | `/pedidos/resumo/` | Estudante | `@estudante_required` | `pedidos/views.py` `resumo_pedido`, linha 151 |
| Detalhe do pedido | `/pedidos/<pk>/` | Estudante (dono) | Filtro `estudante=request.user` | `pedidos/views.py` `pedido_detalhe`, linha 186 |
| Download anexo | `/pedidos/anexo/<pk>/` | Vários (ver _pode_descarregar) | Verificação de papel/etapa/visibilidade | `pedidos/views.py` `_pode_descarregar`, linhas 196-222 |
| Fila | `/pedidos/staff/fila/` | Staff (secretaria, crédito, registo, admin) | `@staff_required` + papel na view | `pedidos/views.py` `fila`, linha 296 |
| Pesquisa | `/pedidos/staff/pesquisa/` | Secretaria / Admin | Verificação na view | `pedidos/views.py` `pesquisa`, linha 358 |
| Detalhe staff | `/pedidos/staff/<pk>/` | Staff (com restrição de etapa) | Verificação de papel/etapa | `pedidos/views.py` `pedido_staff_detalhe`, linha 594 |
| Aprovar | `/pedidos/staff/<pk>/aprovar/` | Staff | `@staff_required` + `pode_decidir` | `pedidos/views.py` `aprovar`, linha 657 |
| Indeferir | `/pedidos/staff/<pk>/indeferir/` | Staff | `@staff_required` + `pode_decidir` | `pedidos/views.py` `indeferir`, linha 675 |
| Marcar pronto | `/pedidos/staff/<pk>/marcar-pronto/` | Staff | `@staff_required` + `pode_decidir` | `pedidos/views.py` `marcar_pronto`, linha 693 |
| Marcar entregue | `/pedidos/staff/<pk>/marcar-entregue/` | Staff | `@staff_required` + `pode_decidir` | `pedidos/views.py` `marcar_entregue`, linha 707 |
| Carregar extracto | `/pedidos/staff/<pk>/carregar-extracto/` | Crédito / Admin | Verificação `e_admin` ou `credito` | `pedidos/views.py` `carregar_extracto`, linha 726 |
| Painel | `/painel/` | Secretaria / Admin | Verificação `e_admin` ou `secretaria` | `pedidos/views.py` `painel`, linhas 447-454 |
| Admin Django | `/admin/` | Staff / Superuser | Django admin (staff_required) | `contas/admin.py`, `pedidos/admin.py` |

## 8.2 Decoradores de permissão

Definidos em `contas/permissoes.py`:

| Decorador | Papéis permitidos | Ficheiro / Linha |
| --- | --- | --- |
| `estudante_required` | `estudante` | linha 46 |
| `secretaria_required` | `secretaria` | linha 47 |
| `credito_required` | `credito` | linha 48 |
| `registo_required` | `registo` | linha 49 |
| `staff_required` | `secretaria`, `credito`, `registo`, `admin` | linha 57 |
| `admin_required` | `admin` | linha 58 |

Todos os decoradores levantam `PermissionDenied` quando o utilizador não tem
permissão, o que faz com que o Django use o template `403.html` temático.

**Ficheiro:** `contas/permissoes.py`, função `_decorador` (linhas 31-43).

## 8.3 Funções auxiliares de autorização

| Função | Descrição | Ficheiro / Linha |
| --- | --- | --- |
| `papel_utilizador(user)` | Devolve o papel do utilizador ou None | `contas/permissoes.py`, linhas 8-14 |
| `e_admin(user)` | True se superutilizador ou papel `admin` | `contas/permissoes.py`, linhas 17-22 |
| `pode_decidir(user, pedido)` | True se admin ou papel da etapa actual | `pedidos/services.py`, linhas 31-41 |
| `_pode_descarregar(utilizador, anexo)` | Verifica acesso a anexo por papel/etapa | `pedidos/views.py`, linhas 196-222 |

## 8.4 Middleware de perfil

`CompletarPerfilMiddleware` redirecciona estudantes com perfil incompleto
(ou sem número de estudante) para `completar_perfil`. Não afecta staff nem
admin.

**Ficheiro:** `contas/middleware.py`, linhas 17-65.

---
*Todos os factos são extraídos do código real do projecto.*