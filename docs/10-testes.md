# 10. Testes

## 10.1 Resultado real da execução da suíte

Comando executado: `python manage.py test`

```
Ran 96 tests in 82.978s
OK
Destroying test database for alias 'default'...
Found 96 test(s).
System check identified no issues (0 silenced).
```

**Resultado: 96 testes executados, 96 aprovados, 0 falhas, 0 erros.**

A base de dados de teste é SQLite partilhada em memória
(`file:memorydb_default?mode=memory&cache=shared`), configurada pelo Django
em ambiente de teste.

## 10.2 Ficheiros de teste

| Ficheiro | App | Descrição |
| --- | --- | --- |
| `contas/tests.py` | contas | Testes de perfis, cursos, importação de utilizadores, decoradores, signals |
| `contas/test_fase4.py` | contas | Testes de throttling de login (3 testes) |
| `contas/test_urls.py` | contas | URLs auxiliares para testes de decoradores |
| `pedidos/tests.py` | pedidos | Testes de tipos, seed, pedidos, anexos, staff |
| `pedidos/test_fase3.py` | pedidos | Testes da fase 3 (filas, decisões, entrega e emails) |
| `pedidos/test_fase4.py` | pedidos | Testes da fase 4 (painel, backup, paginação, páginas de erro) |

## 10.3 Lista de testes por classe

### `contas/tests.py`

Classes principais (extraídas do ficheiro):

- `PerfilTests` — criação e actualização de perfis, número de estudante a partir do email.
- `CursoTests` — criação de cursos, constraint nome+grau.
- `ImportarUtilizadoresTests` — importação por CSV, idempotência, linhas ignoradas.
- `DecoradoresPermissoesTests` — cada devolve 403 ao papel errado; admin passa em todos; superutilizador passa nos decoradores de staff.
- `SignalsTests` — criação automática de Perfil ao criar User.

### `contas/test_fase4.py`

| Método | O que verifica |
| --- | --- |
| (3 testes de throttle) | Limite de tentativas por username e IP; bloqueio de 15 min; sucesso limpa contador do username |

### `pedidos/tests.py`

| Classe | Métodos principais | O que verifica |
| --- | --- | --- |
| `TipoDocumentoTaxasTests` | `test_total_dos_sete_tipos` | Taxa total (base + IVA) dos 7 tipos para licenciatura |
| | `test_iva_usa_a_percentagem_configurada` | IVA usa a percentagem configurada |
| | `test_taxas_base_por_grau` | Taxas base por grau (lic., mest., dout.) |
| `SeedDemoTests` | `test_seed_demo_e_idempotente` | Seed é idempotente |
| | `test_seed_demo_cria_contas_e_dados_academicos` | Contas demo criadas com papéis correctos |
| | `test_seed_demo_cria_as_taxas_esperadas` | Taxas dos tipos de documento |
| | `test_seed_demo_cria_pedidos_com_dois_anexos_cada` | 8 pedidos, 16 anexos, várias etapas |
| `PedidoEstudanteTests` | `test_submissao_valida_cria_pedido_protocolo_e_dois_anexos` | Submissão cria pedido, protocolo, 2 anexos, valor_total = tipo.total(grau) |
| | `test_anexos_invalidos_sao_rejeitados_sem_criar_nada` | Anexos inválidos rejeitados |
| | `test_falta_de_um_dos_anexos_obrigatorios_e_rejeitada` | Falta de anexo rejeitada |
| | `test_tipo_inactivo_nao_aparece_nem_e_aceite` | Tipo inactivo não aparece nem é aceite |
| | `test_estudante_sem_perfil_completo_e_redireccionado` | Sem perfil completo → redireccionado |
| | `test_outro_estudante_recebe_404_no_detalhe_e_no_anexo` | Outro estudante recebe 404 |
| | `test_dono_descarrega_anexos_visiveis_e_nao_os_ocultos` | Download de anexos visíveis; ocultos dão 404 |
| | `test_utilizador_sem_sessao_e_redireccionado_para_o_login` | Sem sessão → login |
| | `test_valor_total_fica_congelado_quando_a_taxa_muda` | Valor congelado se taxa mudar depois |
| | `test_endpoint_htmx_devolve_a_taxa_certa_para_cada_grau` | Endpoint HTMX devolve taxa correcta por grau |
| | `test_meus_pedidos_ordena_do_mais_recente_para_o_mais_antigo` | Ordenação por data |
| | `test_nenhuma_rota_serve_a_pasta_media` | Nenhuma rota serve media/ |
| | `test_nao_aparece_formulario_em_contexto_de_taxa` | Palavra "formulário" não aparece em contexto de taxa |
| `AnexoDownloadStaffTests` | `test_credito_so_descarrega_na_etapa_credito` | Crédito só descarrega na etapa crédito |
| | `test_registo_so_descarrega_na_etapa_registo` | Registo só descarrega na etapa registo |
| | `test_secretaria_e_admin_descarregam_sempre` | Secretaria e admin descarregam sempre |
| `ValidacaoAnexosTests` | `test_aceita_assinaturas_correspondentes` | Aceita PDF, JPG, PNG válidos |
| | `test_rejeita_assinatura_que_nao_bate_com_a_extensao` | Rejeita assinatura binária que não bate com extensão |

### `pedidos/test_fase4.py`

| Classe | Método | O que verifica |
| --- | --- | --- |
| `PainelTests` | `test_painel_so_abre_a_secretaria_e_ao_admin` | Acesso ao painel restrito |
| | `test_totais_e_tempo_medio_batem_com_os_dados_criados` | Cartões e tempo médio correctos |
| | `test_filtro_de_periodo_invalido_e_ignorado_sem_erro_500` | Período inválido ignorado sem erro 500 |
| | `test_painel_nao_mostra_nomes_nem_emails_de_estudantes` | Sem dados pessoais no painel |
| `BackupTests` | `test_comando_cria_zip_com_base_e_anexos` | ZIP com db.sqlite3 e media/ |
| | `test_opcao_manter_apaga_os_backups_mais_antigos` | Retenção de backups |
| `PaginacaoTests` | `test_meus_pedidos_pagina_25_e_pagina_fora_do_limite` | Paginação 25 em meus_pedidos |
| | `test_listas_vazias_nao_partem_a_paginacao` | Listas vazias não quebram paginação |
| | `test_fila_do_pessoal_tambem_pagina_25` | Paginação 25 na fila |
| `PaginasErroTests` | `test_pagina_403_usa_o_tema_e_devolve_o_codigo_certo` | 403 com tema UCM |
| | `test_pagina_404_usa_o_tema_e_devolve_o_codigo_certo` | 404 com tema UCM |
| | `test_404_nao_revela_um_recurso_sem_acesso` | 404 não revela protocolo/nome/email |

## 10.4 Matriz requisito x teste

| Requisito | Testes que cobrem |
| --- | --- |
| RF01 - Submeter pedido | `PedidoEstudanteTests.test_submissao_valida...` |
| RF02 - Tipo, motivo, 2 anexos | `PedidoEstudanteTests.test_submissao_valida...` |
| RF03 - Validação de anexos | `ValidacaoAnexosTests`, `PedidoEstudanteTests.test_anexos_invalidos...` |
| RF04 - Valor congelado | `PedidoEstudanteTests.test_valor_total_fica_congelado...` |
| RF05 - Protocolo | `PedidoEstudanteTests.test_submissao_valida...` |
| RF06 - Resumo da taxa (HTMX) | `PedidoEstudanteTests.test_endpoint_htmx_devolve_a_taxa_certa...` |
| RF07 - Meus pedidos paginados | `PaginacaoTests.test_meus_pedidos_pagina_25...` |
| RF08 - Detalhe do pedido | `PedidoEstudanteTests.test_submissao_valida...` (ver detalhe) |
| RF09 - Download anexos | `PedidoEstudanteTests.test_dono_descarrega_anexos...` |
| RF10 - 404 para outros/ocultos | `PedidoEstudanteTests.test_outro_estudante_recebe_404...` |
| RF11-RF15 - Tratamento staff | `pedidos/test_fase3.py` (filas, decisões, entrega) |
| RF16 - Painel secretaria | `PainelTests.test_painel_so_abre_a_secretaria_e_ao_admin` |
| RF17-RF19 - Crédito | `pedidos/test_fase3.py`, `AnexoDownloadStaffTests` |
| RF20-RF21 - Registo | `pedidos/test_fase3.py` |
| RF22 - Admin decide qualquer etapa | `DecoradoresPermissoesTests` (admin passa em todos) |
| RF23 - Painel/pesquisa admin | `PainelTests`, `pedidos/test_fase3.py` |
| RF24 - Gestão utilizadores | `contas/tests.py` (Perfil, importação) |
| RF25 - Tipos de documento | `pedidos/admin.py` (TipoDocumentoAdmin), `TipoDocumentoTaxasTests` |
| RF26 - Login clássico | `contas/test_fase4.py` (throttling) |
| RF27 - Login Google | `contas/adapters.py` (validação de domínio) — sem teste dedicado visível |
| RF28 - Limite de tentativas | `contas/test_fase4.py` |
| RF29 - Sucesso limpa contador | `contas/test_fase4.py` |
| RF30 - Senha não nos logs | Revisão de código de `contas/views.py` (logger não registra password) |
| RF31 - Backup | `BackupTests.test_comando_cria_zip_com_base_e_anexos` |

**Nota:** Não há teste dedicado para o login Google (RF27) nem para a regra
RNF30 (senhas nos logs) como teste automatizado; são verificados por revisão
de código.

---
*Resultado real obtido executando `python manage.py test` no projecto.*