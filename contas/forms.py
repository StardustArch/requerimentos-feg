from django import forms

from .models import Perfil


class CompletarPerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ("grau", "curso", "numero_estudante", "telefone")
        widgets = {
            "grau": forms.Select(attrs={"class": "form-select"}),
            "curso": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: Informática de Gestão",
                }
            ),
            "numero_estudante": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: 2023001234",
                }
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ex.: 84 000 0000",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["grau"].required = True
        self.fields["curso"].required = True
        self.fields["grau"].empty_label = "Selecione o grau"
