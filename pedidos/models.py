from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models

CENTAVOS = Decimal("0.01")


def _decimal(valor):
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def _arredondar(valor):
    return _decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP)


class TipoDocumento(models.Model):
    GRAUS = ("licenciatura", "mestrado", "doutoramento")

    nome = models.CharField(max_length=150, unique=True)
    taxa_licenciatura = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_mestrado = models.DecimalField(max_digits=10, decimal_places=2)
    taxa_doutoramento = models.DecimalField(max_digits=10, decimal_places=2)
    passa_registo_academico = models.BooleanField(default=False)
    prazo_estimado_dias = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Prazo estimado em dias úteis.",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Tipo de documento"
        verbose_name_plural = "Tipos de documento"

    def __str__(self):
        return self.nome

    def taxa_base(self, grau):
        taxas = {
            "licenciatura": self.taxa_licenciatura,
            "mestrado": self.taxa_mestrado,
            "doutoramento": self.taxa_doutoramento,
        }
        try:
            taxa = taxas[grau]
        except KeyError:
            raise ValueError(f"Grau inválido: {grau!r}") from None
        return _arredondar(taxa)

    def iva(self, grau):
        percentagem = _decimal(settings.IVA_PERCENT) / Decimal("100")
        return _arredondar(self.taxa_base(grau) * percentagem)

    def total(self, grau):
        percentagem = _decimal(settings.IVA_PERCENT) / Decimal("100")
        return _arredondar(self.taxa_base(grau) * (Decimal("1") + percentagem))

    def total_com_formulario(self, grau):
        taxa_formulario = _decimal(settings.TAXA_FORMULARIO)
        percentagem = _decimal(settings.IVA_PERCENT) / Decimal("100")
        formulario_com_iva = taxa_formulario * (Decimal("1") + percentagem)
        return _arredondar(self.total(grau) + formulario_com_iva)
