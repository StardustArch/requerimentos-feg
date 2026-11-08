from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("novo/", views.novo_pedido, name="novo_pedido"),
    path("meus/", views.meus_pedidos, name="meus_pedidos"),
    path("resumo/", views.resumo_pedido, name="resumo_pedido"),
    path("anexo/<int:pk>/", views.anexo_download, name="anexo_download"),
    path("staff/fila/", views.fila, name="fila"),
    path("staff/pesquisa/", views.pesquisa, name="pesquisa"),
    path(
        "staff/<int:pk>/",
        views.pedido_staff_detalhe,
        name="pedido_staff_detalhe",
    ),
    path("staff/<int:pk>/aprovar/", views.aprovar, name="aprovar"),
    path("staff/<int:pk>/indeferir/", views.indeferir, name="indeferir"),
    path(
        "staff/<int:pk>/marcar-pronto/",
        views.marcar_pronto,
        name="marcar_pronto",
    ),
    path(
        "staff/<int:pk>/marcar-entregue/",
        views.marcar_entregue,
        name="marcar_entregue",
    ),
    path(
        "staff/<int:pk>/carregar-extracto/",
        views.carregar_extracto,
        name="carregar_extracto",
    ),
    path("<int:pk>/", views.pedido_detalhe, name="pedido_detalhe"),
]
