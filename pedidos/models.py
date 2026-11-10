import os
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.core.exceptions import ValidationError
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
    indeferido_na_etapa = models.CharField(
        max_length=30,
        choices=ETAPA_CHOICES,
        blank=True,
        default="",
    )
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
        if self.estado == self.ESTADO_INDEFERIDO:
            return "Indeferido"
        if self.estado == self.ESTADO_PRONTO:
            return "Pronto para levantamento"
        if self.estado == self.ESTADO_ENTREGUE:
            return "Entregue"
        return self.get_etapa_actual_display()

    @property
    def dias_na_fila(self):
        return max((timezone.now() - self.criado_em).days, 0)

    # Rótulos curtos para a barra de progresso, por ordem de ETAPAS_APROVACAO.
    ROTULO_ETAPA = {
        ETAPA_SECRETARIA_RECEPCAO: "Secretaria",
        ETAPA_CREDITO: "Crédito",
        ETAPA_REGISTO: "Registo",
        ETAPA_SECRETARIA_FINAL: "Assinatura",
    }

    @property
    def progresso(self):
        """Devolve os dados da barra de progresso por pedido.

        As etapas aplicáveis são as de ETAPAS_APROVACAO, saltando o Registo
        quando TipoDocumento.passa_registo_academico for False. O histórico
        vem de Decisao (pedido.decisoes), nunca de deduções por texto.

        Retorna um dicionário com:
          segmentos: lista de {valor, nome, estado} (estado in
            concluida | actual | pendente | recusada)
          indice_actual: índice da etapa atual (ou None)
          total: número de etapas aplicáveis
          rotulo: texto curto ("etapa X de Y", "Pronto para levantamento",
            "Entregue", "Indeferido")
        """
        from .services import ETAPAS_APROVACAO

        # Etapas de aprovacao (ETAPAS_APROVACAO) mais a etapa final de
        # assinatura (secretaria_final), que nao e de aprovacao mas fecha o
        # fluxo. Nenhuma outra lista de etapas e inventada.
        base = list(ETAPAS_APROVACAO)
        if not self.tipo.passa_registo_academico:
            base = [v for v in base if v != self.ETAPA_REGISTO]
        valores = base + [self.ETAPA_SECRETARIA_FINAL]

        total = len(valores)
        estado = self.estado
        etapa_atual = self.etapa_actual
        indeferido_na_etapa = self.indeferido_na_etapa or ""

        # Histórico de decisões por etapa (fonte de datas para a variante full).
        decisoes_por_etapa = {
            d.etapa: d for d in self.decisoes.all()
        }

        try:
            indice_actual = valores.index(etapa_atual)
        except ValueError:
            indice_actual = None

        indefer_idx = (
            valores.index(indeferido_na_etapa)
            if indeferido_na_etapa in valores
            else None
        )

        if estado == self.ESTADO_EM_TRATAMENTO and indice_actual is not None:
            aria_valuenow = indice_actual
            etapa_actual_nome = self.ROTULO_ETAPA[valores[indice_actual]]
        elif estado in (self.ESTADO_PRONTO, self.ESTADO_ENTREGUE):
            aria_valuenow = total
            etapa_actual_nome = None
        elif estado == self.ESTADO_INDEFERIDO and indefer_idx is not None:
            aria_valuenow = indefer_idx
            etapa_actual_nome = valores[indefer_idx]
        else:
            aria_valuenow = 0
            etapa_actual_nome = None

        segmentos = []
        for i, valor in enumerate(valores):
            nome = self.ROTULO_ETAPA[valor]
            concluida = actual = pendente = recusada = False

            if estado == self.ESTADO_INDEFERIDO and indefer_idx is not None:
                if i == indefer_idx:
                    recusada = True
                elif i < indefer_idx:
                    concluida = True
                else:
                    pendente = True
            elif estado in (self.ESTADO_PRONTO, self.ESTADO_ENTREGUE):
                concluida = True
            elif estado == self.ESTADO_EM_TRATAMENTO and indice_actual is not None:
                if i < indice_actual:
                    concluida = True
                elif i == indice_actual:
                    actual = True
                else:
                    pendente = True
            else:
                pendente = True

            decisao = decisoes_por_etapa.get(valor)
            segmentos.append(
                {
                    "valor": valor,
                    "nome": nome,
                    "estado": (
                        "concluida"
                        if concluida
                        else "actual"
                        if actual
                        else "recusada"
                        if recusada
                        else "pendente"
                    ),
                    "concluida": concluida,
                    "actual": actual,
                    "pendente": pendente,
                    "recusada": recusada,
                    "decisao": decisao,
                }
            )

        return {
            "segmentos": segmentos,
            "indice_actual": indice_actual,
            "total": total,
            "aria_valuenow": aria_valuenow,
            "etapa_actual_nome": etapa_actual_nome,
            "rotulo": self._rotulo_progresso(
                estado, indice_actual, total, indefer_idx, valores
            ),
        }

    def _rotulo_progresso(self, estado, indice_actual, total, indefer_idx, valores):
        if estado == self.ESTADO_PRONTO:
            return "Pronto para levantamento"
        if estado == self.ESTADO_ENTREGUE:
            return "Entregue"
        if estado == self.ESTADO_INDEFERIDO and indefer_idx is not None:
            return f"Indeferido em {valores[indefer_idx]}"
        if estado == self.ESTADO_EM_TRATAMENTO and indice_actual is not None:
            return f"etapa {indice_actual + 1} de {total}"
        return ""

    def save(self, *args, **kwargs):
        e_novo = self._state.adding

        if e_novo:
            if not self.grau and self.estudante_id:
                self.grau = self.estudante.perfil.grau
            # A taxa fica congelada no momento da criação do pedido.
            self.valor_total = self.tipo.total(self.grau)

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


class DecisaoImutavelError(ValidationError, ValueError):
    """Erro levantado quando se tenta alterar ou apagar uma decisão."""


class Decisao(models.Model):
    RESULTADO_APROVADO = "aprovado"
    RESULTADO_INDEFERIDO = "indeferido"
    RESULTADO_PRONTO = "pronto"
    RESULTADO_ENTREGUE = "entregue"

    RESULTADO_CHOICES = (
        (RESULTADO_APROVADO, "Aprovado"),
        (RESULTADO_INDEFERIDO, "Indeferido"),
        (RESULTADO_PRONTO, "Pronto"),
        (RESULTADO_ENTREGUE, "Entregue"),
    )

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.PROTECT,
        related_name="decisoes",
    )
    etapa = models.CharField(max_length=30, choices=Pedido.ETAPA_CHOICES)
    resultado = models.CharField(max_length=20, choices=RESULTADO_CHOICES)
    justificacao = models.TextField(blank=True, default="")
    decidido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decisoes",
    )
    data_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data_hora", "pk"]
        verbose_name = "Decisão"
        verbose_name_plural = "Decisões"

    def __str__(self):
        return (
            f"{self.pedido} — {self.get_etapa_display()}: "
            f"{self.get_resultado_display()}"
        )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise DecisaoImutavelError(
                "Uma decisão registada não pode ser alterada."
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise DecisaoImutavelError(
            "Uma decisão registada não pode ser apagada."
        )
