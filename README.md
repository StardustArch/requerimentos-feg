# Pedidos de Documentos · UCM-FEG

Sistema de pedidos de documentos para a Faculdade de Economia e Gestão da
Universidade Católica de Moçambique. Os estudantes submetem pedidos e os
documentos são entregues fisicamente na secretaria.

Esta é a **Fase 4**: painel de indicadores, limite de tentativas de login,
backups, páginas de erro temáticas, paginação, limites de anexos e verificação
de implantação.

## Requisitos

- Python 3.12+
- Dependências em `requirements.txt` (Django 6.1 e django-allauth)

## Instalação

```bash
cd /home/sdust/Projects/requerimentos

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

### Compilar o CSS (Tailwind)

O CSS é gerado com o Tailwind CLI standalone a partir de `static/css/input.css`:

```bash
# Build de produção (minificado)
./static/tailwindcss -i static/css/input.css -o static/css/app.css --minify

# Modo watch para desenvolvimento
./static/tailwindcss -i static/css/input.css -o static/css/app.css --watch
```

O ficheiro `tailwind.config.js` na raiz define os tokens da marca (roxo UCM como
`brand-700` com escala 50–900), neutros slate, e semânticas por estado do
requerimento.

A aplicação fica disponível em <http://127.0.0.1:8000/>.

O catálogo de cursos pode ser carregado (ou actualizado) isoladamente com
`python manage.py carregar_cursos`. O comando é idempotente e o `seed_demo`
também o executa.

## Variáveis de ambiente

| Variável | Default | Descrição |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | chave de desenvolvimento | Chave secreta do Django. Obrigatória em produção. |
| `DJANGO_DEBUG` | `True` | `False` activa as configurações de segurança (HTTPS, cookies seguros, etc.). |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Lista de hosts separada por vírgulas. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | vazio | Origens confiáveis para CSRF (ex.: `https://requerimentos.ucm.ac.mz`). |
| `SITE_URL` | vazio | URL público do site, usado em links absolutos. |
| `GOOGLE_CLIENT_ID` | vazio | Client ID OAuth do Google. Sem este valor o botão Google fica escondido. |
| `GOOGLE_CLIENT_SECRET` | vazio | Client Secret OAuth do Google. |
| `ALLOWED_EMAIL_DOMAINS` | `ucm.ac.mz,estudante.ucm.ac.mz` | Domínios de email autorizados, separados por vírgulas. |
| `IVA_PERCENT` | `5` | Percentagem de IVA aplicada às taxas. |
| `MAX_ANEXO_MB` | `5` | Tamanho máximo de cada anexo, em megabytes. |
| `DEMO_PASSWORD` | `demo123` | Palavra-passe das contas criadas por `seed_demo`. |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Backend de email. Em produção use o backend SMTP do Django. |
| `EMAIL_HOST` | `localhost` | Servidor SMTP. |
| `EMAIL_PORT` | `25` | Porta SMTP. |
| `EMAIL_USE_TLS` | `False` | Activa TLS na ligação SMTP (`True`/`False`). |
| `EMAIL_HOST_USER` | vazio | Utilizador do servidor SMTP. |
| `EMAIL_HOST_PASSWORD` | vazio | Palavra-passe do servidor SMTP. |
| `DEFAULT_FROM_EMAIL` | `Pedidos UCM-FEG <nao-responder@ucm.ac.mz>` | Remetente das notificações. |
| `LEVANTAMENTO_INFO` | `na Secretaria da Faculdade` | Texto do email de "pronto" que indica onde levantar o documento. |
| `ATENDIMENTO_PRESENCIAL_INFO` | `Dirige-te à Secretaria da Faculdade e faz o pedido presencialmente.` | Texto mostrado quando o curso não aparece na lista ou não é possível identificar o número de estudante. |
| `BACKUP_DIR` | `backups/` (dentro do projeto) | Pasta onde o comando `fazer_backup` guarda os ZIPs. |
| `CACHE_BACKEND` | `django.core.cache.backends.locmem.LocMemCache` | Backend de cache usado pelo throttling de login. |
| `CACHE_LOCATION` | `login-throttle` | Identificador da cache de throttling. |
| `LOGIN_MAX_FALHAS_USERNAME` | `5` | Falhas máximas por username na janela antes de bloquear. |
| `LOGIN_MAX_FALHAS_IP` | `20` | Falhas máximas por IP na janela antes de bloquear. |
| `LOGIN_JANELA_MINUTOS` | `15` | Janela de tempo (minutos) para contagem de falhas e duração do bloqueio. |
| `DJANGO_HSTS_SECONDS` | `3600` | Duração do cabeçalho HSTS em produção. |
| `DJANGO_HSTS_INCLUDE_SUBDOMAINS` | `True` | Inclui subdomínios no HSTS. |
| `DJANGO_HSTS_PRELOAD` | `True` | Adiciona o domínio à lista de pré-carregamento HSTS. |
| `DJANGO_SECURE_SSL_REDIRECT` | `True` | Redireciona HTTP para HTTPS em produção. |

Exemplo para produção:

```bash
export DJANGO_DEBUG=False
export DJANGO_SECRET_KEY='uma-chave-longa-e-aleatoria'
export DJANGO_ALLOWED_HOSTS='requerimentos.ucm.ac.mz'
export DJANGO_CSRF_TRUSTED_ORIGINS='https://requerimentos.ucm.ac.mz'
export SITE_URL='https://requerimentos.ucm.ac.mz'
export GOOGLE_CLIENT_ID='...'
export GOOGLE_CLIENT_SECRET='...'
export DEMO_PASSWORD='uma-palavra-passe-forte'
export EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
export EMAIL_HOST='smtp.ucm.ac.mz'
export EMAIL_PORT='587'
export EMAIL_USE_TLS='True'
export EMAIL_HOST_USER='requerimentos@ucm.ac.mz'
export EMAIL_HOST_PASSWORD='...'
export DEFAULT_FROM_EMAIL='Pedidos UCM-FEG <requerimentos@ucm.ac.mz>'
export LEVANTAMENTO_INFO='na Secretaria da Faculdade'
export ATENDIMENTO_PRESENCIAL_INFO='Dirige-te à Secretaria da Faculdade e faz o pedido presencialmente.'
```

## Login

- **Google institucional**: apenas emails verificados dos domínios definidos em
  `ALLOWED_EMAIL_DOMAINS` (por omissão `ucm.ac.mz` e
  `estudante.ucm.ac.mz`). A validação do domínio é feita no servidor.
- **Login clássico**: para pessoal da faculdade e contas de demonstração.
  - É aplicado um limite de tentativas: **5 falhas por username** ou **20 falhas por IP** numa janela de 15 minutos bloqueiam novas tentativas por 15 minutos. Um login bem-sucedido limpa o contador do username.
  - O Google OAuth não é afectado por este limite.
  - As palavras-passe nunca são escritas nos logs.

No Google Cloud Console, configure o URI de redireccionamento autorizado:

```text
https://<domínio>/accounts/google/login/callback/
```

## Fluxo dos pedidos

O percurso normal de um pedido é:

```text
secretaria_recepcao
  -> credito
  -> registo (só quando o tipo exige confirmação académica)
  -> secretaria_final (aguarda assinatura da direcção, fora do sistema)
  -> pronto
  -> entregue
```

Quem faz o quê:

| Etapa / estado | Papel responsável | Acção |
| --- | --- | --- |
| `secretaria_recepcao` | Secretaria | Aprovar (envia para o crédito) ou indeferir. |
| `credito` | Controlo de Crédito | Confirmar o pagamento, carregar extracto se necessário, aprovar ou indeferir. |
| `registo` | Registo Académico | Confirmar o percurso académico, aprovar ou indeferir. |
| `secretaria_final` | Secretaria | Acompanhar a assinatura da direcção e marcar como pronto. |
| `pronto` | Secretaria | Registar a entrega física do documento. |
| `indeferido` | Qualquer etapa | Pára o pedido. O estudante tem de submeter um novo pedido. |

Cada decisão fica registada de forma imutável, com a etapa, o resultado, a
justificação, o autor e a data/hora. O administrador pode decidir em qualquer
etapa. A secretaria e o administrador vêem qualquer pedido; o crédito e o
registo só vêem os pedidos que estão na sua própria etapa.

Quando um pedido fica **pronto** ou é **indeferido**, o estudante recebe um
email. O envio é feito depois de a decisão estar gravada; se o servidor de email
falhar, a falha fica no log e a decisão mantém-se.

## Contas de demonstração

Criadas por `python manage.py seed_demo` (idempotente):

| Utilizador | Papel | Palavra-passe |
| --- | --- | --- |
| `admin` | Administrador (superutilizador) | `demo123` |
| `secretaria1` | Secretaria | `demo123` |
| `credito1` | Controlo de Crédito | `demo123` |
| `registo1` | Registo Académico | `demo123` |
| `estudante1` | Estudante | `demo123` |

A conta `estudante1` usa o email `701234567@example.com`; o número de
estudante (`701234567`) é extraído automaticamente do email. Tem ainda curso e
grau preenchidos. Se `DEMO_PASSWORD` não for definida, o comando mostra um aviso
por estar a usar a palavra-passe de demonstração.

O `seed_demo` também cria oito pedidos de exemplo para `estudante1`, um em cada
fase do fluxo (secretaria, crédito, registo, secretaria final, pronto e
entregue) e dois indeferidos, um pela secretaria e outro pelo crédito. Cada
pedido tem uma cópia de BI em PDF e um comprovativo em PNG gerados pelo próprio
comando, e as decisões são criadas através dos serviços da aplicação.

## Tipos de documento

`seed_demo` cria sete tipos com as taxas base (licenciatura/mestrado/
doutoramento), indicação de passagem pelo Registo Académico e prazo estimado
em dias úteis:

| Documento | Lic. | Mest. | Dout. | Registo | Prazo |
| --- | ---: | ---: | ---: | :---: | ---: |
| Declaração simples | 100 | 200 | 300 | Não | — |
| Declaração de notas | 200 | 300 | 400 | Sim | — |
| Certificado normal | 2500 | 5000 | 10000 | Sim | 15 |
| Certificado normal (2.ª via) | 5000 | 7500 | 12500 | Sim | 15 |
| Certificado urgente | 5000 | 10000 | 20000 | Sim | 5 |
| Diploma normal | 2000 | 3000 | 10000 | Não | 15 |
| Conteúdos programáticos | 700 | 1400 | 2100 | Não | — |

Os valores são base, sem IVA. O total é calculado com `IVA_PERCENT`.

O valor de cada pedido fica congelado no momento da submissão, em
`Pedido.valor_total`. Como a taxa do formulário (apenas aplicável ao pedido
físico em papel) foi removida, os pedidos criados anteriormente mantêm o
valor antigo que incluía essa taxa. Em desenvolvimento, refaça a base de dados
com `python manage.py seed_demo` para obter pedidos com o valor correcto
(só taxa do tipo + IVA).

## Anexos e ficheiros sensíveis

Cada pedido obriga à submissão de dois anexos: a cópia do BI e o comprovativo
de pagamento. São aceites apenas ficheiros **PDF, JPG/JPEG ou PNG** até
`MAX_ANEXO_MB` (5 MB por omissão). A validação verifica os primeiros bytes do
ficheiro, pelo que renomear um ficheiro para `.pdf` não é suficiente.

Os ficheiros são guardados em `media/pedidos/<ano>/` com um nome aleatório
(UUID) e apenas a extensão original. O nome enviado pelo utilizador é guardado
separadamente em `nome_original` para aparecer na descarga e nunca é usado no
caminho.

Esta pasta **não é pública**: não é configurado um `MEDIA_URL` público nem
existe qualquer rota que sirva `media/` directamente. As descargas passam
todas pela vista `pedidos:anexo_download`, que confirma quem está autenticado
e qual o seu papel antes de entregar o ficheiro. Um pedido de outro estudante
ou um anexo não visível responde com **404**, para não revelar a existência do
ficheiro.

Os extractos bancários carregados pelo Controlo de Crédito são internos: só o
próprio crédito (enquanto o pedido está nessa etapa) e o administrador os podem
descarregar. A secretaria, o registo e o estudante recebem **404** nesses
anexos.

Como os anexos são dados sensíveis e não podem ser reconstruídos a partir da
base de dados, a pasta `media/` (ou o volume/bucket usado em produção) precisa
de **cópia de segurança regular**, em conjunto com a base de dados.

## Importar utilizadores

```bash
python manage.py importar_utilizadores caminho/para/utilizadores.csv
```

O CSV deve ter as colunas `nome,email,papel` e pode incluir `curso,grau`. Não
existe coluna de número de estudante: para estudantes, o número é sempre
extraído do início da parte local do email institucional (por exemplo,
`701234567@estudante.ucm.ac.mz`). Linhas de estudantes cujo email não comece
por um número são ignoradas e reportadas como erro; o resto da importação
continua. O comando é idempotente e só gera palavras-passe para contas novas.
Use `--sem-password` para contas que entram apenas por Google.

## Backups

O comando `fazer_backup` cria um ZIP com uma cópia consistente da base de dados
SQLite (via `sqlite3.Connection.backup`) e com a pasta `media/` (anexos e
extractos):

```bash
python manage.py fazer_backup           # guarda backups/backup-YYYYMMdd-HHMMSS.zip
python manage.py fazer_backup --manter 7   # mantém apenas os 7 mais recentes
```

A cada execução o comando imprime o nome do ficheiro, o tamanho e quantos
backups permanecem, e remove automaticamente os mais antigos além de `--manter`
(por omissão 14).

Em produção, agende execuções diárias. Exemplo de `crontab`:

```crontab
0 2 * * * cd /home/suaconta/requerimentos && /caminho/para/.venv/bin/python manage.py fazer_backup --manter 14 >> /caminho/para/logs/backup.log 2>&1
```

No PythonAnywhere, use a tarefa "Scheduled Task" diária com o comando acima,
ajustando o caminho do virtualenv e do projeto. Não se esqueça de definir
`BACKUP_DIR` para uma pasta fora do código-fonte (ex. `/home/suaconta/backups`).

### Restauro

O ZIP contém `db.sqlite3` e `media/`. Para restaurar:

1. Descompacte o backup: `unzip backups/backup-....zip -d restauro/`
2. Substitua a base de dados: `cp restauro/db.sqlite3 db.sqlite3`
3. Restaure os ficheiros: `cp -r restauro/media/* media/`
4. Reinicie a aplicação.

O ficheiro `backups/` está no `.gitignore` e nunca deve ser commitado.

## Painel de indicadores

O painel fica em `/painel/` e é acessível apenas à Secretaria e ao
Administrador. Apresenta:

- Cartões com o total de pedidos no período, separados por estado actual.
- Gráficos (Chart.js, renderizados com `json_script`) de pedidos por estado,
  indeferimentos ao longo do tempo e tempo médio de tratamento por tipo de
  documento.
- Tabelas com a fila actual e os 10 tipos com maior tempo médio de tratamento.

O período é filtrado por parâmetro GET `periodo` (ex. `30d`, `90d`, `tudo`);
valores inválidos são ignorados sem erro. O painel nunca exibe nomes, emails ou
números de estudante.

## Páginas de erro

As respostas 403, 404 e 500 usam templates com o tema visual da UCM-FEG
(`ucm-topbar`) e um link para voltar à página inicial. A página 404 não revela
a existência de recursos a que o utilizador não tem acesso.

## Paginação e limites de anexos

- `Meus pedidos` e a `Fila` são paginados de 25 em 25.
- O formulário de novo pedido mostra o tamanho máximo de anexo (`MAX_ANEXO_MB`)
  e os tipos de ficheiro aceites (PDF, JPG/JPEG, PNG).

## Implantação (`check --deploy`)

Em produção defina `DJANGO_DEBUG=False` e as variáveis de ambiente acima. Execute:

```bash
DJANGO_DEBUG=False ... python manage.py check --deploy
```

Deve passar sem avisos. Decisões de implantação ainda pendentes:

- Escolher o backend de cache em produção (por omissão usa `LocMemCache`, que não é partilhada entre processos; em servidores com vários workers prefira Redis/Memcached).
- Definir `BACKUP_DIR` para um volume/persistente separado do código-fonte.
- Confirmar o valor de `DJANGO_HSTS_SECONDS` antes de activar `PRELOAD` (um domínio pré-carregado é difícil de remover).

## Testes

```bash
python manage.py check
python manage.py test
```
