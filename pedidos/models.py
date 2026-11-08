import os
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.utils import timezone

from contas.models import Perfil

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


def caminho_anexo(instance, filename):
    """Devolve um caminho imprevisível para o ficheiro anexado.

    O nome enviado pelo utilizador nunca é usado no caminho. Só a extensão
    original é preservada, e mesmo essa é normalizada para minúsculas.
    """

    extensao = os.path.splitext(filename)[1].lower()
    ano = timezone.localdate().year
    if instance.pedido_id and instance.pedido.criado_em:
        ano = instance.pedido.criado_em.year
    return f"pedidos/{ano}/{uuid.uuid4().hex}{extensao}"


class Pedido(models.Model):
    ESTADO_EM_TRATAMENTO = "em_tratamento"
    ESTADO_INDEFERIDO = "indeferido"
    ESTADO_PRONTO = "pronto"
    ESTADO_ENTREGUE = "entregue"

    ESTADO_CHOICES = (
        (ESTADO_EM_TRATAMENTO, "Em tratamento"),
        (ESTADO_INDEFERIDO, "Indeferido"),
        (ESTADO_PRONTO, "Pronto"),
        (ESTADO_ENTREGUE, "Entregue"),
    )

    ETAPA_SECRETARIA_RECEPCAO = "secretaria_recepcao"
    ETAPA_CREDITO = "credito"
    ETAPA_REGISTO = "registo"
    ETAPA_SECRETARIA_FINAL = "secretaria_final"

    ETAPA_CHOICES = (
        (ETAPA_SECRETARIA_RECEPCAO, "Na secretaria"),
        (ETAPA_CREDITO, "No controlo de crédito"),
        (ETAPA_REGISTO, "No registo académico"),
        (ETAPA_SECRETARIA_FINAL, "Aguarda assinatura da direcção"),
    )

    protocolo = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        default="",
    )
    estudante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    tipo = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    grau = models.CharField(max_length=20, choices=Perfil.GRAU_CHOICES)
    motivo = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_EM_TRATAMENTO,
    )
    etapa_actual = models.CharField(
        max_length=30,
        choices=ETAPA_CHOICES,
        default=ETAPA_SECRETARIA_RECEPCAO,
    )
    motivo_indeferimento = models.TextField(blank=True, default="")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)
    pronto_em = models.DateTimeField(blank=True, null=True)
    entregue_em = models.DateTimeField(blank=True, null=True)
    entregue_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pedidos_entregues",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return self.protocolo or f"Pedido #{self.pk or 'novo'}"

    @property
    def etapa_simples(self):
        return self.get_etapa_actual_display()

    def save(self, *args, **kwargs):
        e_novo = self._state.adding

        if e_novo:
            if not self.grau and self.estudante_id:
                self.grau = self.estudante.perfil.grau
            # A taxa fica congelada no momento da criação do pedido.
            self.valor_total = self.tipo.total_com_formulario(self.grau)

        super().save(*args, **kwargs)

        if e_novo:
            self.protocolo = f"REQ-{timezone.localdate().year}-{self.pk:05d}"
            super().save(update_fields=["protocolo"])


class Anexo(models.Model):
    TIPO_BI = "bi"
    TIPO_COMPROVATIVO = "comprovativo"
    TIPO_EXTRACTO = "extracto"
    TIPO_OUTRO = "outro"

    TIPO_CHOICES = (
        (TIPO_BI, "Cópia do BI"),
        (TIPO_COMPROVATIVO, "Comprovativo de pagamento"),
        (TIPO_EXTRACTO, "Extracto bancário"),
        (TIPO_OUTRO, "Outro"),
    )

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="anexos",
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    ficheiro = models.FileField(upload_to=caminho_anexo)
    nome_original = models.CharField(max_length=255)
    visivel_ao_estudante = models.BooleanField(default=False)
    carregado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="anexos_carregados",
    )
    carregado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["carregado_em"]
        verbose_name = "Anexo"
        verbose_name_plural = "Anexos"

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.nome_original}"
