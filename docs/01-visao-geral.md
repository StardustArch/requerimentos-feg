# 01. Visão geral — Cap. I (Introdução) e secção 5.1

## 1.1 Objectivo do sistema

O **Pedidos de Documentos · UCM-FEG** é uma plataforma Web de gestão de
requerimentos (pedidos de documentos) para a Faculdade de Economia e Gestão
da Universidade Católica de Moçambique (UCM-FEG). O sistema permite que
estudantes submetam pedidos de documentos académicos (certificados,
declarações, diplomas, etc.), anexem os ficheiros obrigatórios (cópia do BI
e comprovativo de pagamento) e acompanhem o estado do pedido até à entrega
física do documento.

Pessoal da faculdade (Secretaria, Controlo de Crédito, Registo Académico e
Administração) trata os pedidos em fila de trabalho, aprovando, indeferindo
ou marcando como pronto/entregue, registando decisões imutáveis com
justificação.

**Evidência:** `templates/contas/home.html`, `README.md` (descrição do
sistema), `config/settings.py` (docstring do ficheiro).

## 1.2 Problema que resolve (deduzido do fluxo real)

Antes da plataforma, os pedidos de documentos eram feitos presencialmente e
o acompanhamento do estado de cada requerimento era manual. O sistema
resolve os seguintes problemas, deduzidos do fluxo implementado:

- Os estudantes precisam de um canal para submeter pedidos e anexar
  comprovativos sem deslocar-se apenas para entregar papel (`pedidos/views.py`,
  `novo_pedido`, linhas 90-146).
- A faculdade precisa de separar o tratamento por departamento (Secretaria →
  Crédito → Registo → Secretaria final), com cada departamento vendo apenas
  os pedidos na sua etapa (`pedidos/views.py`, `fila`, linhas 295-354;
  `pedidos/services.py`, `PAPEIS_POR_ETAPA`, linhas 23-28).
- É necessário registar decisões de forma imutável para auditoria, com
  justificação, autor e data/hora (`pedidos/models.py`, `Decisao`, linhas
  234-283).
- É preciso notificar o estudante quando o pedido fica pronto ou é
  indeferido (`pedidos/notificacoes.py`, `notificar_estudante`, linhas 43-79).
- O acesso deve ser restrito por papel, com páginas de erro temáticas e
  limite de tentativas de login (`contas/views.py`, `LoginViewComLimite`,
  linhas 59-121; `templates/403.html`, `404.html`, `500.html`).

## 1.3 Perfis de utilizador

Os papéis estão definidos em `contas/models.py`, classe `Perfil`, linhas
58-70:

| Papel | Constante | Descrição |
| --- | --- | --- |
| Estudante | `PAPEL_ESTUDANTE` | Submete pedidos, acompanha o estado e faz download dos seus anexos |
| Secretaria | `PAPEL_SECRETARIA` | Trata recepção, assinatura final e entrega |
| Controlo de Crédito | `PAPEL_CREDITO` | Valida pagamentos e carrega extractos |
| Registo Académico | `PAPEL_REGISTO` | Valida percurso académico quando exigido |
| Administrador | `PAPEL_ADMIN` | Acesso total, painel, pesquisa e administração |

A função `papel_utilizador(user)` em `contas/permissoes.py` (linhas 8-14)
devolve o papel do utilizador autenticado. A função `e_admin(user)` (linhas
17-22) considera admin quem é superutilizador ou tem papel `admin`.

## 1.4 Stack e versões

| Componente | Versão | Fonte |
| --- | --- | --- |
| Python | 3.12+ | `requirements.txt` / ambiente `.venv` |
| Django | 6.1.3 | `requirements.txt` linha 6 |
| django-allauth | 65.21.1 | `requirements.txt` linha 7 |
| Base de dados | SQLite 3 | `config/settings.py` linha 135 |
| Frontend | Tailwind CSS v4 (compilado localmente) | `static/css/app.css` (de `static/css/input.css` via `tailwind.config.js`) |
| Interatividade | Unpoly | `static/vendor/unpoly/unpoly.min.js` |
| Gráficos | Chart.js | `static/vendor/chartjs/chart.umd.min.js` |
| Ícones | Lucide SVG (embutidos) | `templates/components/icon.html` |
| Fonte | Inter local | `static/fonts/*.woff2` (`@font-face`) |
| Autenticação social | Google OAuth (django-allauth) | `config/settings.py` linhas 235-262 |

## 1.5 Estrutura de pastas (resumo)

Ver `docs/00-varredura.md` secção 3 para o inventário completo comentado.

Pastas principais:
- `config/` — configuração do Django
- `contas/` — app de contas, perfis, autenticação
- `pedidos/` — app de pedidos, tipos, anexos, decisões
- `templates/` — templates Django
- `static/` — ficheiros estáticos (CSS, imagens, vendor)
- `media/` — anexos enviados (não servido publicamente)
- `docs/` — dossier técnico

## 1.6 Como instalar e correr

1. Criar e activar o ambiente virtual:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Executar migrações:
   ```bash
   python manage.py migrate
   ```
4. Carregar dados de demonstração (cursos, utilizadores, tipos e pedidos):
   ```bash
   python manage.py seed_demo
   ```
5. Compilar o CSS do Tailwind (obrigatório antes de correr o servidor):
   ```bash
   python manage.py tailwind build
   ```
   Ou, diretamente com o binário CLI:
   ```bash
   ./static/tailwindcss -i static/css/input.css -o static/css/app.css --minify
   ```
   Para desenvolvimento em modo watch: `python manage.py tailwind watch`.
   O ficheiro `tailwind.config.js` na raiz define os tokens da marca (roxo UCM como
   `brand-700`, escala 50–900), neutros slate e cores semânticas por estado.
6. Iniciar o servidor de desenvolvimento:
   ```bash
   python manage.py runserver
   ```
7. Aceder a `http://127.0.0.1:8000/`.

**Evidência:** `README.md` secção "Compilar o CSS (Tailwind)" e "Instalação",
`manage.py`, `config/settings.py` (`TAILWIND_*`), `tailwind.config.js`.

### Variáveis de ambiente relevantes

| Variável | Default | Descrição |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | chave de desenvolvimento | Chave secreta do Django |
| `DJANGO_DEBUG` | `True` | Modo de depuração |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost` | Hosts permitidos |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | vazio | Origens confiáveis para CSRF |
| `SITE_URL` | vazio | URL público do site |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | vazio | Credenciais OAuth do Google |
| `ALLOWED_EMAIL_DOMAINS` | `ucm.ac.mz,estudante.ucm.ac.mz` | Domínios autorizados |
| `IVA_PERCENT` | `5` | Percentagem de IVA |
| `MAX_ANEXO_MB` | `5` | Tamanho máximo de anexo (MB) |
| `DEMO_PASSWORD` | `demo123` | Palavra-passe das contas demo |
| `EMAIL_BACKEND` | console | Backend de email |
| `BACKUP_DIR` | `backups/` | Pasta de cópias de segurança |

(`config/settings.py` linhas 26-309)

## 1.7 Utilizadores de demonstração (seed)

O comando `python manage.py seed_demo` (`pedidos/management/commands/seed_demo.py`)
cria os seguintes utilizadores (**idempotente**):

| Utilizador | Papel | Email | Palavra-passe |
| --- | --- | --- | --- |
| `admin` | Administrador (superutilizador) | `admin@ucm.ac.mz` | `demo123` (ou `DEMO_PASSWORD`) |
| `secretaria1` | Secretaria | `secretaria1@ucm.ac.mz` | `demo123` |
| `credito1` | Controlo de Crédito | `credito1@ucm.ac.mz` | `demo123` |
| `registo1` | Registo Académico | `registo1@ucm.ac.mz` | `demo123` |
| `estudante1` | Estudante | `701234567@example.com` | `demo123` |

**Evidência:** `pedidos/management/commands/seed_demo.py`, `UTILIZADORES_DEMO`,
linhas 112-146.

O `seed_demo` também cria 7 tipos de documento e 8 pedidos de exemplo para
`estudante1`, cobrindo as diferentes etapas do fluxo (secretaria, crédito,
registo, secretaria final, pronto, entregue, e dois indeferidos).

**Evidência:** `pedidos/management/commands/seed_demo.py`, `TIPOS_DOCUMENTO`
(linhas 53-110) e `PEDIDOS_DEMO` (linhas 148-210).

---
*Todos os factos são extraídos do código real do projecto.*