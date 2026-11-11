from django import forms

from contas.form_mixins import StyledFormMixin
from contas.widgets import StyledFileInput
from .models import Pedido, TipoDocumento
from .validators import validar_anexo

ACCEPT_ANEXOS = ".pdf,.jpg,.jpeg,.png"


class NovoPedidoForm(StyledFormMixin, forms.ModelForm):
    anexo_bi = forms.FileField(
        label="Cópia do BI",
        validators=[validar_anexo],
        widget=StyledFileInput(attrs={"accept": ACCEPT_ANEXOS}),
    )
    anexo_comprovativo = forms.FileField(
        label="Comprovativo de pagamento",
        validators=[validar_anexo],
        widget=StyledFileInput(attrs={"accept": ACCEPT_ANEXOS}),
    )

    class Meta:
        model = Pedido
        fields = ("tipo", "motivo")
        widgets = {
            "tipo": forms.Select(),
            "motivo": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Explica brevemente para que precisas do documento.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo"].queryset = TipoDocumento.objects.filter(activo=True)
        self.fields["tipo"].empty_label = "Selecione o tipo de documento"
        self.fields["motivo"].required = True
        self.fields["anexo_bi"].required = True
        self.fields["anexo_comprovativo"].required = True
