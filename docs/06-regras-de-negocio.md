# 06. Regras de negócio — secção 5.6

Todas as regras abaixo são extraídas do código real do projecto, com
referência ao ficheiro e função que as implementam.

## 6.1 Ciclo de vida do requerimento

O pedido começa no estado `em_tratamento` e etapa `secretaria_recepcao`.
Pode terminar em `indeferido`, `pronto` ou `entregue`.

**Ficheiro:** `pedidos/models.py`, classes `Pedido.ESTADO_CHOICES` (linhas
88-93) e `Pedido.ETAPA_CHOICES` (linhas 100-105).

## 6.2 Transições de estado permitidas

As transições só são possíveis quando o pedido está em
`em_tratamento`. Cada transição usa bloqueio pessimista
(`select_for_update`) para evitar condições de corrida.

| Etapa actual | Actor | Acção | Resultado |
| --- | --- | --- | --- |
| `secretaria_recepcao` | Secretaria / Admin | aprovar | Avança para `credito` |
| `secretaria_recepcao` | Secretaria / Admin | indeferir | Estado `indeferido` |
| `credito` | Crédito / Admin | aprovar | `registo` se `passa_registo_academico`, senão `secretaria_final` |
| `credito` | Crédito / Admin | indeferir | Estado `indeferido` |
| `registo` | Registo / Admin | aprovar | Avança para `secretaria_final` |
| `registo` | Registo / Admin | indeferir | Estado `indeferido` |
| `secretaria_final` | Secretaria / Admin | marcar_pronto | Estado `pronto` |
| `pronto` | Qualquer staff | marcar_entregue | Estado `entregue` |

**Ficheiro:** `pedidos/services.py`,
- `aprovar` (linhas 82-114): define a próxima etapa com base na etapa actual
  e em `passa_registo_academico`.
- `indeferir` (linhas 117-150): requer motivo com pelo menos 10 caracteres.
- `marcar_pronto` (linhas 153-176): apenas na etapa `secretaria_final`.
- `marcar_entregue` (linhas 179-202): apenas se o estado for `pronto`.
- `_bloquear` (linhas 44-49): `select_for_update` no pedido.

## 6.3 O que cada departamento pode fazer

As regras de papel por etapa estão em `PAPEIS_POR_ETAPA`:

| Etapa | Papel responsável |
| --- | --- |
| `secretaria_recepcao` | Secretaria |
| `credito` | Controlo de Crédito |
| `registo` | Registo Académico |
| `secretaria_final` | Secretaria |

O Administrador (ou superutilizador) pode decidir em qualquer etapa
(`pode_decidir` retorna `True` para admin).

**Ficheiro:** `pedidos/services.py`,
- `PAPEIS_POR_ETAPA` (linhas 23-28).
- `pode_decidir` (linhas 31-41).

## 6.4 Validações

### 6.4.1 Submissão de pedido
- Tipo de documento deve ser activo.
- Dois anexos obrigatórios: cópia do BI e comprovativo de pagamento.
- Anexos devem ser PDF, JPG/JPEG ou PNG.
- Tamanho máximo de cada anexo: `MAX_ANEXO_MB` (default 5 MB).
- Validação por assinatura binária (primeiros bytes), não apenas extensão.

**Ficheiro:** `pedidos/forms.py` (linhas 9-45),
`pedidos/validators.py`, `validar_anexo` (linhas 32-63).

### 6.4.2 Indeferimento
- O motivo é obrigatório e deve ter pelo menos 10 caracteres.

**Ficheiro:** `pedidos/services.py`, `indeferir` (linhas 120-125).

### 6.4.3 Login
- 5 falhas por username ou 20 por IP numa janela de 15 minutos bloqueiam
  novas tentativas por 15 minutos.
- Sucesso de login limpa apenas o contador do username.
- Google OAuth não é afectado pelo limite de tentativas.
- Palavras-passe nunca são escritas nos logs.

**Ficheiro:** `contas/views.py`,
- `_limites_login` (linhas 44-49).
- `_login_bloqueado` (linhas 52-56).
- `_incrementar_faltas` (linhas 33-41).
- `LoginViewComLimite.post` (linhas 64-121).

## 6.5 Cálculos de taxas e pagamentos

O valor de um pedido é: taxa base do tipo para o grau do estudante + IVA.

| Cálculo | Fórmula | Ficheiro / Linha |
| --- | --- | --- |
| Taxa base | `taxa_licenciatura` / `taxa_mestrado` / `taxa_doutoramento` | `pedidos/models.py`, `taxa_base`, linhas 48-58 |
| IVA | `taxa_base * (IVA_PERCENT / 100)` | `pedidos/models.py`, `iva`, linhas 60-62 |
| Total | `taxa_base * (1 + IVA_PERCENT / 100)` | `pedidos/models.py`, `total`, linhas 64-66 |
| Valor congelado | `tipo.total(grau)` no momento da criação | `pedidos/models.py`, `Pedido.save`, linha 183 |

`IVA_PERCENT` default é 5 (variável de ambiente).

**Ficheiro:** `config/settings.py`, linha 272.

Nota: a taxa de formulário (`TAXA_FORMULARIO`) foi removida; o valor de um
pedido é só a taxa do tipo para o grau, mais IVA.

## 6.6 Histórico e auditoria

- Cada decisão (aprovar, indeferir, pronto, entregue) fica registada de
  forma imutável na tabela `Decisao`, com etapa, resultado, justificação,
  autor (`decidido_por`) e data/hora.
- Decisões não podem ser alteradas nem apagadas (`DecisaoImutavelError`).
- O envio de email de notificação (pronto / indeferido) é agendado após o
  commit da transação (`transaction.on_commit`). Se o email falhar, a
  decisão mantém-se e a falha é registada no log.

**Ficheiro:** `pedidos/models.py`, `Decisao.save`/`delete` (linhas 273-283);
`pedidos/services.py`, `_registar_decisao` (linhas 66-73),
`_agendar_notificacao` (linhas 76-79);
`pedidos/notificacoes.py`, `notificar_estudante` (linhas 43-79).

## 6.7 Permissões por perfil

| Perfil | Pode submeter pedidos | Pode ver fila | Pode decidir | Pode ver painel | Pode gerir utilizadores |
| --- | --- | --- | --- | --- | --- |
| Estudante | Sim (próprios) | Não | Não | Não | Não |
| Secretaria | Não | Sim (recepção, assinatura, prontos) | Na sua etapa | Sim | Não |
| Crédito | Não | Sua etapa | Na sua etapa | Não | Não |
| Registo | Não | Sua etapa | Na sua etapa | Não | Não |
| Admin | Não | Todas | Qualquer etapa | Sim | Sim (via admin Django) |

Mecanismo: decoradores em `contas/permissoes.py`
(`estudante_required`, `secretaria_required`, `credito_required`,
`registo_required`, `staff_required`, `admin_required`) e verificação
direta nas views (`e_admin`, `pode_decidir`).

**Ficheiro:** `contas/permissoes.py` (linhas 8-58),
`pedidos/views.py` (verificações de papel nas views).

## 6.8 Anexos e visibilidade

- Anexos do tipo `extracto` são internos: visíveis apenas a Crédito (enquanto
  o pedido está na etapa crédito) e Admin.
- Anexos `bi` e `comprovativo` são visíveis ao estudante dono e à Secretaria.
- Qualquer outro utilizador que tente aceder a um anexo sem permissão
  recebe 404 (não se revela a existência do ficheiro).

**Ficheiro:** `pedidos/views.py`, `_pode_descarregar` (linhas 196-222).

---
*Todos os factos são extraídos do código real do projecto.*