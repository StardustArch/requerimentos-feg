# 02. Requisitos — secção 2.4

## 2.4.1 Actores do sistema

Os actores são os perfis de utilizador definidos no modelo `Perfil`
(`contas/models.py`, linhas 57-116) e as regras de permissão
(`contas/permissoes.py`).

| Actor | Descrição | Fonte |
| --- | --- | --- |
| Estudante | Utilizador com papel `estudante`. Submete pedidos, anexa ficheiros, consulta o estado dos seus pedidos e faz download dos anexos visíveis. Precisa de perfil completo (curso e número de estudante). | `contas/models.py`, `Perfil` |
| Secretaria | Utilizador com papel `secretaria`. Trata a recepção de pedidos, aprova ou indefere na primeira etapa, aguarda assinatura da direcção, marca como pronto e regista a entrega física. | `contas/models.py`, `Perfil` |
| Controlo de Crédito | Utilizador com papel `credito`. Valida o pagamento dos pedidos na sua etapa e carrega extractos bancários. | `contas/models.py`, `Perfil` |
| Registo Académico | Utilizador com papel `registo`. Valida o percurso académico quando o tipo de documento o exigir (`passa_registo_academico`). | `contas/models.py`, `Perfil` |
| Administrador | Utilizador com papel `admin` (ou superutilizador). Acesso total: filas, pesquisa, painel, administração e decisão em qualquer etapa. | `contas/models.py`, `Perfil` |
| Visitante / não autenticado | Pode ver a página de login e a página inicial (redireccionada). Não tem acesso a funcionalidades do sistema. | `contas/views.py`, `contas/urls.py` |

## 2.4.2 Requisitos funcionais

Cada requisito funcional é identificado com um código `RFxx` e citada a view/rota
que o implementa.

### RF — Submissão de requerimentos (Estudante)

| ID | Requisito | View / Rota | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF01 | O estudante autenticado com perfil completo pode submeter um novo pedido de documento. | `pedidos.views.novo_pedido` | `pedidos/views.py` linhas 90-146 |
| RF02 | O pedido requer tipo de documento, motivo e dois anexos (cópia do BI e comprovativo de pagamento). | `pedidos.forms.NovoPedidoForm` | `pedidos/forms.py` linhas 9-45 |
| RF03 | Os anexos devem ser PDF, JPG/JPEG ou PNG, com tamanho máximo de `MAX_ANEXO_MB` (5 MB), validados por extensão, tamanho e assinatura binária. | `pedidos.validators.validar_anexo` | `pedidos/validators.py` linhas 32-63 |
| RF04 | O valor do pedido fica congelado no momento da submissão (taxa do tipo + IVA). | `Pedido.save` | `pedidos/models.py` linhas 176-189 |
| RF05 | O estudante recebe um protocolo no formato `REQ-AAAA-NNNNN`. | `Pedido.save` | `pedidos/models.py` linhas 187-189 |
| RF06 | O estudante pode consultar o resumo da taxa (base, IVA, total) via HTMX ao escolher o tipo. | `pedidos.views.resumo_pedido` | `pedidos/views.py` linhas 151-161 |

### RF — Acompanhamento (Estudante)

| ID | Requisito | View / Rota | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF07 | O estudante lista os seus pedidos paginados (25 por página). | `pedidos.views.meus_pedidos` | `pedidos/views.py` linhas 166-177 |
| RF08 | O estudante vê o detalhe do seu pedido (estado, etapa, anexos, valor). | `pedidos.views.pedido_detalhe` | `pedidos/views.py` linhas 182-193 |
| RF09 | O estudante faz download dos seus anexos visíveis. | `pedidos.views.anexo_download` | `pedidos/views.py` linhas 226-252 |
| RF10 | Um pedido de outro estudante ou um anexo não visível responde com 404 (não revela existência). | `pedidos.views.pedido_detalhe`, `anexo_download` | `pedidos/views.py` linhas 182-193, 226-252 |

### RF — Tratamento pela Secretaria (Staff)

| ID | Requisito | View / Rota | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF11 | A secretaria vê a fila de pedidos novos e de assinatura. | `pedidos.views.fila` | `pedidos/views.py` linhas 295-354 |
| RF12 | A secretaria aprova um pedido (avança para crédito ou secretaria final). | `pedidos.services.aprovar` | `pedidos/services.py` linhas 82-114 |
| RF13 | A secretaria indefere um pedido com justificação de pelo menos 10 caracteres. | `pedidos.services.indeferir` | `pedidos/services.py` linhas 117-150 |
| RF14 | A secretaria marca o pedido como pronto (apenas na etapa secretaria final). | `pedidos.services.marcar_pronto` | `pedidos/services.py` linhas 153-176 |
| RF15 | A secretaria regista a entrega física do documento. | `pedidos.services.marcar_entregue` | `pedidos/services.py` linhas 179-202 |
| RF16 | A secretaria vê o painel de indicadores. | `pedidos.views.painel` | `pedidos/views.py` linhas 442-580 |

### RF — Controlo de Crédito (Staff)

| ID | Requisito | View / Rota | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF17 | O crédito vê a fila de pedidos na sua etapa. | `pedidos.views.fila` | `pedidos/views.py` linhas 334-340 |
| RF18 | O crédito aprova ou indefere o pedido na sua etapa. | `pedidos.services.aprovar`, `indeferir` | `pedidos/services.py` linhas 82-150 |
| RF19 | O crédito carrega o extracto bancário do pedido. | `pedidos.views.carregar_extracto` | `pedidos/views.py` linhas 722-757 |

### RF — Registo Académico (Staff)

| ID | Requisito | View / Rota | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF20 | O registo vê a fila de pedidos na sua etapa (apenas tipos com `passa_registo_academico`). | `pedidos.views.fila` | `pedidos/views.py` linhas 341-347 |
| RF21 | O registo aprova ou indefere o pedido na sua etapa. | `pedidos.services.aprovar`, `indeferir` | `pedidos/services.py` linhas 82-150 |

### RF — Administração

| ID | Requisito | View / Rota | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF22 | O admin decide em qualquer etapa (bypassa a regra de papel por etapa). | `pedidos.services.pode_decidir` | `pedidos/services.py` linhas 31-41 |
| RF23 | O admin acede ao painel de indicadores e à pesquisa de pedidos. | `pedidos.views.painel`, `pesquisa` | `pedidos/views.py` linhas 442-580, 357-406 |
| RF24 | O admin gere utilizadores e perfis via admin do Django. | `contas.admin.PerfilAdmin` | `contas/admin.py` linhas 7-32 |
| RF25 | O admin gere tipos de documento, taxas e prazos via admin do Django. | `pedidos.admin.TipoDocumentoAdmin` | `pedidos/admin.py` linhas 77-97 |

### RF — Autenticação e segurança

| ID | Requisito | View / Rota | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF26 | Login clássico (username/password) para pessoal e contas de demonstração. | `contas.views.LoginViewComLimite` | `contas/views.py` linhas 59-121 |
| RF27 | Login Google institucional com validação de domínio no servidor. | `contas.adapters.ContasSocialAccountAdapter` | `contas/adapters.py` linhas 28-113 |
| RF28 | Limite de tentativas: 5 falhas por username ou 20 por IP numa janela de 15 min. | `contas/views.py` `_login_bloqueado`, `_incrementar_faltas` | `contas/views.py` linhas 33-56 |
| RF29 | Sucesso de login limpa o contador do username (não afecta IP nem Google). | `contas.views.LoginViewComLimite.post` | `contas/views.py` linhas 90-94 |
| RF30 | Palavras-passe nunca são escritas nos logs. | `contas/views.py` logger | `contas/views.py` linhas 70-75 |

### RF — Backups e manutenção

| ID | Requisito | Comando | Ficheiro / Linha |
| --- | --- | --- | --- |
| RF31 | Backup consistente SQLite + media/ em ZIP, com retenção configurável (`--manter`). | `fazer_backup` | `pedidos/management/commands/fazer_backup.py` linhas 28-137 |

## 2.4.3 Requisitos não funcionais

| ID | Requisito | Evidência no código |
| --- | --- | --- |
| RNF01 | Segurança: apenas SQLite suportado para backup; ficheiros de media não são servidos publicamente. | `pedidos/management/commands/fazer_backup.py` linha 90-93; `config/settings.py` linhas 215-217 |
| RNF02 | Segurança: HSTS, X-Frame-Options DENY, content-type nosniff, referrer policy, COOP. | `config/settings.py` linhas 48-59 |
| RNF03 | Segurança: cookies de sessão e CSRF seguros em produção (`DEBUG=False`). | `config/settings.py` linhas 61-65 |
| RNF04 | Usabilidade: tema visual UCM-FEG em todas as páginas (topbar, navbar, cards). | `templates/base.html` |
| RNF05 | Usabilidade: páginas de erro 403/404/500 temáticas com link para a página inicial. | `templates/403.html`, `404.html`, `500.html` |
| RNF06 | Usabilidade: paginação de 25 itens em `meus_pedidos` e `fila`. | `pedidos/views.py` linhas 172, 266-268 |
| RNF07 | Portabilidade: configuração via variáveis de ambiente; mesma base de código em dev e produção. | `config/settings.py` (docstring, linhas 1-6) |
| RNF08 | Desempenho: bloqueio otimista com `select_for_update` nas transições de decisão. | `pedidos/services.py` função `_bloquear`, linhas 44-49 |
| RNF09 | Auditoria: decisões são imutáveis (não se alteram nem apagam). | `pedidos/models.py`, `Decisao.save`/`delete`, linhas 273-283 |
| RNF10 | Fiabilidade: falha de envio de email não reverte a decisão (registada no log). | `pedidos/notificacoes.py` linhas 63-78 |

---
*Todos os factos são extraídos do código real do projecto.*