# 04. Diagramas de actividade e sequência — secções 4.3 e 4.4

Os diagramas abaixo são baseados exclusivamente no código real do projecto.
Cada um tem uma explicação curta e a referência ao ficheiro/função.

## 4.1 Diagrama de actividade — Login clássico com limite de tentativas

**Fluxo:** o utilizador submete credenciais; o sistema verifica se o
username ou IP está bloqueado; se não, autentica; em caso de falha,
incrementa contadores e bloqueia se atingir o limite.

**Referência:** `contas/views.py`, `LoginViewComLimite.post` (linhas 64-121),
`_login_bloqueado` (linhas 52-56), `_incrementar_faltas` (linhas 33-41).

```mermaid
flowchart TD
    A[Utilizador acede /contas/login/] --> B[Submete username + password]
    B --> C{Username/IP bloqueado?}
    C -->|Sim| D[Mostrar mensagem de bloqueio<br>Impedir tentativa]
    C -->|Não| E[Autenticar via LoginView]
    E -->|Sucesso| F[Limpar contador de falhas do username]
    E -->|Falha| G[Incrementar contador username e IP]
    G --> H{Atingiu limite 5 user ou 20 IP?}
    H -->|Sim| I[Registar aviso no log<br>Bloquear próximas tentativas]
    H -->|Não| J[Devolver resposta de erro]
    F --> K[Redireccionar para home]
    D --> L[Fim]
    I --> L
    J --> L
    K --> L
```

## 4.2 Diagrama de sequência — Submissão de requerimento (estudante)

**Fluxo:** o estudante preenche o formulário, o resumo da taxa é buscado
via HTMX, e ao submeter o pedido é criado com valor congelado e anexos.

**Referência:** `pedidos/views.py`, `novo_pedido` (linhas 90-146),
`pedidos/models.py`, `Pedido.save` (linhas 176-189),
`pedidos/forms.py`, `NovoPedidoForm` (linhas 9-45),
`pedidos/validators.py`, `validar_anexo` (linhas 32-63).

```mermaid
sequenceDiagram
    autonumber
    participant Estudante
    participant View as novo_pedido (views.py)
    participant HTMX as HTMX /pedidos/resumo/
    participant Form as NovoPedidoForm (forms.py)
    participant Val as validar_anexo (validators.py)
    participant DB as Base de dados SQLite

    Estudante->>View: GET /pedidos/novo/
    View-->>Estudante: Formulário vazio
    Estudante->>HTMX: change no select tipo
    HTMX->>View: GET /pedidos/resumo/?tipo=X
    View->>DB: buscar TipoDocumento
    View-->>HTMX: taxa base, IVA, total
    HTMX-->>Estudante: resumo atualizado
    Estudante->>View: POST /pedidos/novo/ (tipo, motivo, anexos)
    View->>Form: validar dados e ficheiros
    Form->>Val: validar_anexo (extensão, tamanho, assinatura)
    Val-->>Form: OK / erro
    Form-->>View: form válido
    View->>DB: criar Pedido (valor_total congelado)
    DB-->>View: pedido com pk
    View->>DB: criar 2 Anexos (BI + comprovativo)
    View->>DB: gerar protocolo REQ-AAAA-NNNNN
    View-->>Estudante: redireccionar para pedido_detalhe
```

## 4.3 Diagrama de actividade — Passagem entre departamentos (staff)

**Fluxo:** secretaria aprova → crédito; crédito aprova → registo (se
exigir) ou secretaria final; registo aprova → secretaria final;
secretaria final marca pronto; secretaria regista entrega.

**Referência:** `pedidos/services.py`, `aprovar` (linhas 82-114),
`PAPEIS_POR_ETAPA` (linhas 23-28), `ETAPAS_APROVACAO` (linhas 17-21).

```mermaid
flowchart TD
    A[Pedido criado<br>etapa: secretaria_recepcao] --> B[Secretaria aprova?]
    B -->|Sim| C[Etapa: credito]
    B -->|Não (indeferir)| D[Pedido indeferido<br>Fim do fluxo]
    C --> E[Crédito aprova?]
    E -->|Sim| F{passa_registo_academico?}
    F -->|Sim| G[Etapa: registo]
    F -->|Não| H[Etapa: secretaria_final]
    E -->|Não (indeferir)| D
    G --> I[Registo aprova?]
    I -->|Sim| H
    I -->|Não (indeferir)| D
    H --> J[Secretaria marca pronto<br>estado: pronto]
    J --> K[Staff regista entrega<br>estado: entregue]
    K --> L[Fim: documento entregue]
    D --> L
    L --> L
```

## 4.4 Diagrama de sequência — Aprovação de etapa (staff)

**Fluxo:** o membro de staff clica em "Aprovar etapa"; o serviço bloqueia o
pedido (`select_for_update`), verifica permissão e etapa, regista a decisão
e avança para a próxima etapa.

**Referência:** `pedidos/services.py`, `aprovar` (linhas 82-114),
`_bloquear` (44-49), `_exigir_permissao` (52-56), `_exigir_em_tratamento`
(59-63), `_registar_decisao` (66-73).

```mermaid
sequenceDiagram
    autonumber
    participant Staff
    participant View as aprovar (views.py)
    participant Svc as aprovar (services.py)
    participant DB as Base de dados SQLite

    Staff->>View: POST /pedidos/staff/<pk>/aprovar/
    View->>Svc: aprovar(pedido, actor, justificacao)
    Svc->>DB: SELECT ... FOR UPDATE (bloquear pedido)
    DB-->>Svc: pedido bloqueado
    Svc->>Svc: _exigir_permissao (papel da etapa)
    Svc->>Svc: _exigir_em_tratamento (estado)
    Svc->>Svc: _registar_decisao (resultado=aprovado)
    Svc->>DB: INSERT Decisao
    Svc->>DB: UPDATE pedido.etapa_actual = próxima
    Svc-->>View: pedido actualizado
    View-->>Staff: redireccionar para pedido_staff_detalhe
```

## 4.5 Diagrama de sequência — Marcar como pronto e entregar

**Fluxo:** secretaria marca como pronto (apenas em `secretaria_final`);
qualquer staff regista a entrega (apenas se `pronto`). Cada um regista uma
`Decisao` imutável e notifica o estudante (pronto).

**Referência:** `pedidos/services.py`, `marcar_pronto` (153-176),
`marcar_entregue` (179-202); `pedidos/notificacoes.py`, `notificar_estudante`
(43-79).

```mermaid
sequenceDiagram
    autonumber
    participant Secretaria
    participant View as marcar_pronto / marcar_entregue
    participant Svc as services.py
    participant DB as Base de dados SQLite
    participant Email as notificar_estudante (email)

    Secretaria->>View: POST marcar-pronto (etapa secretaria_final)
    View->>Svc: marcar_pronto(pedido, actor)
    Svc->>DB: SELECT ... FOR UPDATE
    Svc->>Svc: verificar etapa = secretaria_final
    Svc->>Svc: _registar_decisao (resultado=pronto)
    Svc->>DB: INSERT Decisao
    Svc->>DB: UPDATE estado=pronto, pronto_em=agora
    Svc->>Email: notificar_estudante (evento=pronto)
    Email-->>Svc: enviado / falha registada no log
    Svc-->>View: pedido pronto
    View-->>Secretaria: redirect detalhe

    note over Secretaria,View: Entrega física (qualquer staff)
    Staff->>View: POST marcar-entregue (estado=pronto)
    View->>Svc: marcar_entregue(pedido, actor)
    Svc->>DB: SELECT ... FOR UPDATE
    Svc->>Svc: verificar estado = pronto
    Svc->>Svc: _registar_decisao (resultado=entregue)
    Svc->>DB: INSERT Decisao
    Svc->>DB: UPDATE estado=entregue, entregue_em, entregue_por
    Svc-->>View: pedido entregue
    View-->>Staff: redirect detalhe
```

## 4.6 Diagrama de sequência — Backup consistente (fazer_backup)

**Fluxo:** o comando cria cópia consistente da SQLite via
`Connection.backup`, adiciona `media/` a um ZIP e remove backups antigos.

**Referência:** `pedidos/management/commands/fazer_backup.py`, `handle`
(linhas 45-86), `_copiar_base` (88-124), `_adicionar_media` (126-137).

```mermaid
sequenceDiagram
    autonumber
    participant Admin
    participant Cmd as fazer_backup (management command)
    participant SQLite as Base de dados SQLite
    participant Media as Pasta media/
    participant ZIP as Ficheiro ZIP de backup
    participant FS as Sistema de ficheiros (BACKUP_DIR)

    Admin->>Cmd: python manage.py fazer_backup [--manter N]
    Cmd->>SQLite: abrir ligação (Django ou sqlite3 direto)
    Cmd->>SQLite: Connection.backup → cópia consistente db.sqlite3
    SQLite-->>Cmd: db.sqlite3 copiado
    Cmd->>Media: ler ficheiros de media/
    Cmd->>ZIP: escrever db.sqlite3 + media/
    Cmd->>FS: guardar ZIP com timestamp
    Cmd->>FS: listar backups existentes
    Cmd->>FS: apagar backups além de --manter
    FS-->>Cmd: backups restantes
    Cmd-->>Admin: nome, tamanho, backups restantes
```

---
*Todos os factos são extraídos do código real do projecto.*