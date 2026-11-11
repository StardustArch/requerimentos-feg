from django import forms

from .form_mixins import StyledFormMixin
from .models import Curso, Perfil


class CompletarPerfilForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ("curso", "telefone")
        widgets = {
            "curso": forms.Select(),
            "telefone": forms.TextInput(
                attrs={
                    "placeholder": "Ex.: 84 000 0000",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["curso"].required = True
        self.fields["curso"].queryset = (
            Curso.objects.filter(activo=True).order_by("grau", "nome")
        )
        self.fields["curso"].empty_label = "Selecione o curso"
        self.fields["telefone"].required = False
