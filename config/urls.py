"""URL configuration for the document request system."""

from django.contrib import admin
from django.urls import include, path

from contas.views import dashboard_redirect
from pedidos.views import painel, styleguide

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("contas/", include("contas.urls")),
    path("painel/", painel, name="painel"),
    path("dev/styleguide/", styleguide, name="styleguide"),
    path("pedidos/", include("pedidos.urls")),
    path("", dashboard_redirect, name="home"),
]
