from django.contrib import admin

from .models import Curso, Perfil


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
        "curso__nome",
    )
    list_editable = ("papel",)
    readonly_fields = ("numero_estudante",)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        # Para além de ser apresentado como leitura, o número é desactivado
        # no formulário: mesmo um POST forjado não o consegue alterar.
        if "numero_estudante" in form.base_fields:
            form.base_fields["numero_estudante"].disabled = True
        return form


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nome", "grau", "activo")
    list_filter = ("grau", "activo")
    list_editable = ("grau", "activo")
    search_fields = ("nome",)
    ordering = ("grau", "nome")
