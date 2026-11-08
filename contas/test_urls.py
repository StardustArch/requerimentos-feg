"""URLs auxiliares usadas apenas pelos testes dos decoradores."""

from django.http import HttpResponse
from django.urls import include, path

from . import views
from .permissoes import (
    admin_required,
    credito_required,
    estudante_required,
    registo_required,
    secretaria_required,
    staff_required,
)


def _resposta_ok(request):
    return HttpResponse("ok")


probe_estudante = estudante_required(_resposta_ok)
probe_secretaria = secretaria_required(_resposta_ok)
probe_credito = credito_required(_resposta_ok)
probe_registo = registo_required(_resposta_ok)
probe_staff = staff_required(_resposta_ok)
probe_admin = admin_required(_resposta_ok)

urlpatterns = [
    path("probe/estudante/", probe_estudante, name="probe_estudante"),
    path("probe/secretaria/", probe_secretaria, name="probe_secretaria"),
    path("probe/credito/", probe_credito, name="probe_credito"),
    path("probe/registo/", probe_registo, name="probe_registo"),
    path("probe/staff/", probe_staff, name="probe_staff"),
    path("probe/admin/", probe_admin, name="probe_admin"),
    path("contas/", include("contas.urls")),
    path("", views.dashboard_redirect, name="home"),
]
