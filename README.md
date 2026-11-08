# Pedidos de Documentos · UCM-FEG

Sistema de pedidos de documentos para a Faculdade de Economia e Gestão da
Universidade Católica de Moçambique. Os estudantes submetem pedidos e os
documentos são entregues fisicamente na secretaria.

Esta é a **Fase 3**: filas de trabalho por departamento, decisões, entrega e
notificações por email ao estudante.

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
| `TAXA_FORMULARIO` | `20` | Valor base do formulário de pedido, sem IVA. |
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

Os valores são base, sem IVA. O total é calculado com `IVA_PERCENT` e o
formulário acrescenta `TAXA_FORMULARIO` (também com IVA).

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

## Testes

```bash
python manage.py check
python manage.py test
```
