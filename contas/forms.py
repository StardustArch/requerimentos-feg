from django import forms

from .models import Curso, Perfil


class CompletarPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ("curso", "telefone")
        widgets = {
            "curso": forms.Select(attrs={"class": "form-select"}),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control",
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
