from django.contrib import admin

from .models import Anexo, Pedido, TipoDocumento


class SomenteLeituraAdmin(admin.ModelAdmin):
    """Permite consultar no admin, mas não criar, alterar ou apagar."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Pedido)
class PedidoAdmin(SomenteLeituraAdmin):
    list_display = (
        "protocolo",
        "estudante",
        "tipo",
        "estado",
        "etapa_actual",
    )
    list_display_links = ("protocolo",)
    list_filter = ("estado", "etapa_actual", "tipo", "grau")
    search_fields = (
        "protocolo",
        "estudante__username",
        "estudante__email",
        "tipo__nome",
    )
    date_hierarchy = "criado_em"


@admin.register(Anexo)
class AnexoAdmin(SomenteLeituraAdmin):
    list_display = (
        "pedido",
        "tipo",
        "nome_original",
        "visivel_ao_estudante",
        "carregado_por",
        "carregado_em",
    )
    list_display_links = ("pedido",)
    list_filter = ("tipo", "visivel_ao_estudante")
    search_fields = (
        "pedido__protocolo",
        "nome_original",
        "carregado_por__username",
    )


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
