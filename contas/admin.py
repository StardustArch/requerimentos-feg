from django.contrib import admin

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "papel",
        "numero_estudante",
        "curso",
        "grau",
        "telefone",
    )
    list_filter = ("papel", "grau")
    search_fields = (
        "user__username",
        "user__email",
        "numero_estudante",
        "curso",
    )
    list_editable = ("papel",)
