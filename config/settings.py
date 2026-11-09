"""
Django settings for the UCM-FEG document request system.

The project is configured through environment variables so that the same
codebase can run in development and in production.
"""

import os
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(nome, default=False):
    valor = os.environ.get(nome)
    if valor is None:
        return default
    return valor.strip().lower() in {"1", "true", "yes", "on"}


# ---------------------------------------------------------------------------
# Core / security
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-requerimentos-%y_p@d!5gg#88$8(d$qv$lvi4*!!wjyhzdy",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"] + [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]

# Cabeçalhos de segurança aplicados em todos os ambientes. O HSTS fica
# desligado em desenvolvimento e usa um valor baixo (1 hora) em produção; pode
# ser aumentado, ou desligado, através de DJANGO_HSTS_SECONDS.
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SECURE_HSTS_SECONDS = int(
    os.environ.get("DJANGO_HSTS_SECONDS", "0" if DEBUG else "3600")
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool(
    "DJANGO_HSTS_INCLUDE_SUBDOMAINS",
    not DEBUG,
)
SECURE_HSTS_PRELOAD = _env_bool("DJANGO_HSTS_PRELOAD", not DEBUG)

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", True)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "contas",
    "pedidos",
    "django_tailwind_cli",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "contas.middleware.CompletarPerfilMiddleware",
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "contas.context_processors.google_oauth",
                "contas.context_processors.atendimento_presencial",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# ---------------------------------------------------------------------------
# Cache e limite de tentativas de login
# ---------------------------------------------------------------------------

# LocMemCache chega para uma única instância. Em vários processos/servidores,
# configure um backend partilhado (por exemplo Redis ou Memcached) através de
# CACHE_BACKEND e CACHE_LOCATION.
CACHES = {
    "default": {
        "BACKEND": os.environ.get(
            "CACHE_BACKEND",
            "django.core.cache.backends.locmem.LocMemCache",
        ),
        "LOCATION": os.environ.get("CACHE_LOCATION", "requerimentos"),
    }
}

LOGIN_MAX_TENTATIVAS_USERNAME = int(
    os.environ.get("LOGIN_MAX_TENTATIVAS_USERNAME", "5")
)
LOGIN_MAX_TENTATIVAS_IP = int(os.environ.get("LOGIN_MAX_TENTATIVAS_IP", "20"))
LOGIN_JANELA_MINUTOS = int(os.environ.get("LOGIN_JANELA_MINUTOS", "15"))


# ---------------------------------------------------------------------------
# Cópias de segurança
# ---------------------------------------------------------------------------

BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", BASE_DIR / "backups"))


# ---------------------------------------------------------------------------
# Authentication / passwords
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "Africa/Maputo"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]


# ---------------------------------------------------------------------------
# Ficheiros enviados pelos utilizadores (anexos)
# ---------------------------------------------------------------------------

# Os anexos são dados sensíveis: ficam fora de STATIC_ROOT e não existe
# qualquer rota pública que sirva esta pasta. Só a vista anexo_download os
# entrega, depois de verificar as permissões.
MEDIA_ROOT = BASE_DIR / "media"
MAX_ANEXO_MB = int(os.environ.get("MAX_ANEXO_MB", "5"))


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------

LOGIN_URL = "/contas/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/contas/login/"


# ---------------------------------------------------------------------------
# Institutional Google login
# ---------------------------------------------------------------------------

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
ALLOWED_EMAIL_DOMAINS = [
    dominio.strip().lower()
    for dominio in os.environ.get(
        "ALLOWED_EMAIL_DOMAINS", "ucm.ac.mz,estudante.ucm.ac.mz"
    ).split(",")
    if dominio.strip()
]

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "contas.adapters.ContasSocialAccountAdapter"
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        # O parâmetro "hd" apenas sugere a conta no ecrã do Google. A
        # validação efetiva do domínio é feita no servidor pelo adapter.
        "AUTH_PARAMS": {
            "hd": ALLOWED_EMAIL_DOMAINS[0] if ALLOWED_EMAIL_DOMAINS else "",
        },
        "APP": {
            "client_id": GOOGLE_CLIENT_ID,
            "secret": GOOGLE_CLIENT_SECRET,
            "key": "",
            "name": "Google",
        },
    }
}

# URL público do site (útil para links absolutos em fases seguintes).
SITE_URL = os.environ.get("SITE_URL", "")


# ---------------------------------------------------------------------------
# Taxas de documentos
# ---------------------------------------------------------------------------

IVA_PERCENT = Decimal(os.environ.get("IVA_PERCENT", "5"))


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "25"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "False").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Pedidos UCM-FEG <nao-responder@ucm.ac.mz>",
)

# Texto mostrado ao estudante quando o documento fica pronto para levantamento.
LEVANTAMENTO_INFO = os.environ.get(
    "LEVANTAMENTO_INFO",
    "na Secretaria da Faculdade",
)

# Indicação de atendimento presencial, usada quando o curso não está na lista
# ou quando não é possível identificar o número de estudante pelo email.
ATENDIMENTO_PRESENCIAL_INFO = os.environ.get(
    "ATENDIMENTO_PRESENCIAL_INFO",
    "Dirige-te à Secretaria da Faculdade e faz o pedido presencialmente.",
)

# ---------------------------------------------------------------------------
# Tailwind CSS (django-tailwind-cli)
# ---------------------------------------------------------------------------
# O CSS compilado é gerado em static/css/app.css a partir de static/css/input.css.
# O ficheiro tailwind.config.js fica na raiz do projeto.
TAILWIND_CLI_PATH = None  # Usa o binário fornecido pelo django-tailwind-cli
TAILWIND_OUTPUT_CSS = "static/css/app.css"
TAILWIND_INPUT_CSS = "static/css/input.css"
TAILWIND_CONFIG_FILE = "tailwind.config.js"
