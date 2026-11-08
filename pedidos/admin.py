from django.contrib import admin

from .models import TipoDocumento


@admin.register(TipoDocumento)
class TipoDocumentoAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "taxa_licenciatura",
        "taxa_mestrado",
        "taxa_doutoramento",
        "passa_registo_academico",
        "prazo_estimado_dias",
        "activo",
    )
    list_display_links = ("nome",)
    list_editable = (
        "taxa_licenciatura",
        "taxa_mestrado",
        "taxa_doutoramento",
        "passa_registo_academico",
        "prazo_estimado_dias",
        "activo",
    )
    list_filter = ("activo", "passa_registo_academico")
    search_fields = ("nome",)
