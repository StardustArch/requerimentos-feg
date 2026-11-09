# 14. Glossário e abreviaturas

## 14.1 Abreviaturas

| Sigla | Significado | Contexto no projecto |
| --- | --- | --- |
| API | Application Programming Interface | Não existe API REST no projecto (deduzido) |
| CRUD | Create, Read, Update, Delete | Padrão de operações (admin do Django) |
| CSS | Cascading Style Sheets | `static/css/ucm-theme.css` |
| ER | Entity-Relationship | Modelo de dados (`docs/05-modelo-de-dados.md`) |
| HTML | HyperText Markup Language | Templates Django |
| HTTP | HyperText Transfer Protocol | Protocolo de comunicação Web |
| IVA | Imposto sobre o Valor Acrescentado | `config/settings.py` linha 272 (`IVA_PERCENT`) |
| MTV | Model-Template-View | Padrão arquitetural do Django (`docs/07-arquitectura.md`) |
| ORM | Object-Relational Mapping | Mapeamento objeto-relacional do Django |
| PK | Primary Key | Chave primária nos modelos Django |
| RF | Requisito Funcional | `docs/02-requisitos.md` |
| RNF | Requisito Não Funcional | `docs/02-requisitos.md` |
| SMTP | Simple Mail Transfer Protocol | Envio de email (`config/settings.py` linhas 279-296) |
| SQL | Structured Query Language | Linguagem de consulta à base de dados |
| SQLite | Base de dados SQL em ficheiro | `config/settings.py` linha 135 |
| UCM | Universidade Católica de Moçambique | Instituição de contexto |
| FEG | Faculdade de Economia e Gestão | Unidade orgânica da UCM |
| UI | User Interface | Interface do utilizador (`templates/`) |
| UML | Unified Modeling Language | Linguagem de modelagem (referência em diagramas) |
| URL | Uniform Resource Locator | Endereço Web (`config/urls.py`, `pedidos/urls.py`) |
| WSGI | Web Server Gateway Interface | Interface do servidor Web (`config/wsgi.py`) |
| ASGI | Asynchronous Server Gateway Interface | Interface assíncrona (`config/asgi.py`) |
| HTMX | HTML over HTTP | Interatividade no formulário de novo pedido (`static/vendor/htmx/`) |
| Chart.js | Biblioteca de gráficos JavaScript | Gráficos do painel (`static/vendor/chartjs/`) |
| Bootstrap | Framework CSS/JS | Estilos e componentes UI (`static/vendor/bootstrap/`) |
| OAuth | Open Authorization | Protocolo de autorização (login Google) |
| JWT | JSON Web Token | Token usado pelo allauth (`PyJWT` em `requirements.txt`) |

## 14.2 Glossário de termos

| Termo | Definição |
| --- | --- |
| Actor | Papel de utilizador no sistema (estudante, secretaria, crédito, registo, admin) |
| Caso de uso | Descrição de uma interação entre actor e sistema para atingir um objetivo |
| Decisão | Registo imutável de aprovação, indeferimento, pronto ou entregue sobre um pedido |
| Etapa | Fase do fluxo de tratamento de um pedido (recepção, crédito, registo, secretaria final) |
| Estado | Situação atual de um pedido (em tratamento, indeferido, pronto, entregue) |
| Protocolo | Identificador único do pedido no formato `REQ-AAAA-NNNNN` |
| Requerimento | Pedido de documento submetido por um estudante (`Pedido`) |
| Tipo de documento | Categoria de documento com taxas por grau e prazo estimado (`TipoDocumento`) |
| Anexo | Ficheiro anexado a um pedido (BI, comprovativo, extracto, outro) |
| Throttling | Limitação de tentativas (de login) para evitar ataques de força bruta |
| Middleware | Componente que processa requisições/respostas entre o servidor e a view |
| Context processor | Função que adiciona variáveis ao contexto de todos os templates |
| Signal | Mecanismo do Django para notificar eventos (ex.: criação de `Perfil` ao criar `User`) |
| Seed | Carregamento de dados iniciais de demonstração (`seed_demo`) |
| Backup | Cópia de segurança consistente da base de dados e ficheiros de media |
| Valor congelado | Valor total do pedido fixado no momento da criação, não alterado se a taxa mudar |
| Perfil completo | Perfil de estudante com curso e número de estudante preenchidos |

## 14.3 Estados do requerimento (valores reais do código)

| Valor | Significado | Ficheiro / Linha |
| --- | --- | --- |
| `em_tratamento` | Pedido a ser tratado | `pedidos/models.py` linha 83 |
| `indeferido` | Pedido rejeitado | `pedidos/models.py` linha 84 |
| `pronto` | Pedido pronto para levantamento | `pedidos/models.py` linha 85 |
| `entregue` | Pedido entregue ao estudante | `pedidos/models.py` linha 86 |

## 14.4 Etapas do requerimento (valores reais do código)

| Valor | Significado | Ficheiro / Linha |
| --- | --- | --- |
| `secretaria_recepcao` | Na secretaria (receção) | `pedidos/models.py` linha 95 |
| `credito` | No controlo de crédito | `pedidos/models.py` linha 96 |
| `registo` | No registo académico | `pedidos/models.py` linha 97 |
| `secretaria_final` | Aguarda assinatura da direcção | `pedidos/models.py` linha 98 |

## 14.5 Resultados de decisão (valores reais do código)

| Valor | Significado | Ficheiro / Linha |
| --- | --- | --- |
| `aprovado` | Etapa aprovada | `pedidos/models.py` linha 235 |
| `indeferido` | Pedido indeferido | `pedidos/models.py` linha 236 |
| `pronto` | Pedido marcado como pronto | `pedidos/models.py` linha 237 |
| `entregue` | Pedido marcado como entregue | `pedidos/models.py` linha 238 |

## 14.6 Papéis de utilizador (valores reais do código)

| Valor | Significado | Ficheiro / Linha |
| --- | --- | --- |
| `estudante` | Estudante | `contas/models.py` linha 58 |
| `secretaria` | Secretaria | `contas/models.py` linha 59 |
| `credito` | Controlo de Crédito | `contas/models.py` linha 60 |
| `registo` | Registo Académico | `contas/models.py` linha 61 |
| `admin` | Administrador | `contas/models.py` linha 62 |

---
*Todos os termos e valores são extraídos do código real do projecto.*