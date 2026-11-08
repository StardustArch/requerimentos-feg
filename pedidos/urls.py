from django.urls import path

from . import views

app_name = "pedidos"

urlpatterns = [
    path("novo/", views.novo_pedido, name="novo_pedido"),
    path("meus/", views.meus_pedidos, name="meus_pedidos"),
    path("resumo/", views.resumo_pedido, name="resumo_pedido"),
    path("anexo/<int:pk>/", views.anexo_download, name="anexo_download"),
    path("<int:pk>/", views.pedido_detalhe, name="pedido_detalhe"),
]
