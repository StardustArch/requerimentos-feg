"""
Django settings for the UCM-FEG document request system.

The project is configured through environment variables so that the same
codebase can run in development and in production.
"""

import os
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


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

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True


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
TAXA_FORMULARIO = Decimal(os.environ.get("TAXA_FORMULARIO", "20"))


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
