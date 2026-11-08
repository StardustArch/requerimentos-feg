from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "contas"

urlpatterns = [
    path(
        "login/",
        views.LoginViewComLimite.as_view(),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "completar-perfil/",
        views.completar_perfil,
        name="completar_perfil",
    ),
]
