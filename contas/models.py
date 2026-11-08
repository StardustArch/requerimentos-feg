import logging
import re

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q


logger = logging.getLogger(__name__)

# Número de estudante: sequência de 6 a 10 dígitos no início da parte local
# do email institucional. A extração não depende do domínio do email.
NUMERO_ESTUDANTE_REGEX = re.compile(r"^(\d{6,10})")


def extrair_numero_estudante(email):
    """Extrai o número de estudante da parte local de um email institucional.

    Devolve o número como string, ou None quando o email não começa por
    dígitos (não há número identificável).
    """
    if not email or "@" not in email:
        return None
    local = email.split("@", 1)[0]
    correspondencia = NUMERO_ESTUDANTE_REGEX.match(local)
    return correspondencia.group(1) if correspondencia else None


class Curso(models.Model):
    """Curso de estudo, pertencente a um grau. Fixa o grau do perfil."""

    GRAU_CHOICES = (
        ("licenciatura", "Licenciatura"),
        ("mestrado", "Mestrado"),
        ("doutoramento", "Doutoramento"),
    )

    nome = models.CharField(max_length=150, unique=True)
    grau = models.CharField(max_length=20, choices=GRAU_CHOICES)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("grau", "nome")
        verbose_name = "curso"
        verbose_name_plural = "cursos"

    def __str__(self):
        return self.nome


class Perfil(models.Model):
    PAPEL_ESTUDANTE = "estudante"
    PAPEL_SECRETARIA = "secretaria"
    PAPEL_CREDITO = "credito"
    PAPEL_REGISTO = "registo"
    PAPEL_ADMIN = "admin"

    PAPEL_CHOICES = (
        (PAPEL_ESTUDANTE, "Estudante"),
        (PAPEL_SECRETARIA, "Secretaria"),
        (PAPEL_CREDITO, "Controlo de Crédito"),
        (PAPEL_REGISTO, "Registo Académico"),
        (PAPEL_ADMIN, "Administrador"),
    )

    GRAU_LICENCIATURA = "licenciatura"
    GRAU_MESTRADO = "mestrado"
    GRAU_DOUTORAMENTO = "doutoramento"

    GRAU_CHOICES = (
        (GRAU_LICENCIATURA, "Licenciatura"),
        (GRAU_MESTRADO, "Mestrado"),
        (GRAU_DOUTORAMENTO, "Doutoramento"),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil"
    )
    papel = models.CharField(
        max_length=20,
        choices=PAPEL_CHOICES,
        default=PAPEL_ESTUDANTE,
    )
    # O número de estudante é sempre derivado do email institucional (veja
    # extrair_numero_estudante). Nunca é preenchido à mão.
    numero_estudante = models.CharField(max_length=30, blank=True, null=True)
    curso = models.ForeignKey(
        Curso,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="perfis",
    )
    grau = models.CharField(
        max_length=20, choices=GRAU_CHOICES, blank=True, null=True
    )
    telefone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["numero_estudante"],
                condition=Q(numero_estudante__isnull=False)
                & ~Q(numero_estudante=""),
                name="unique_numero_estudante_quando_preenchido",
            ),
        ]

    def __str__(self):
        return f"{self.user.username} ({self.get_papel_display()})"

    @property
    def e_estudante(self):
        return self.papel == self.PAPEL_ESTUDANTE

    @property
    def e_admin(self):
        return self.papel == self.PAPEL_ADMIN

    @property
    def perfil_completo(self):
        # Estudante completo: curso escolhido (que fixa o grau) e número de
        # estudante identificado a partir do email.
        return bool(self.curso_id and self.numero_estudante)

    def save(self, *args, **kwargs):
        if self.papel == self.PAPEL_ESTUDANTE:
            email = getattr(self.user, "email", "") or ""
            numero = extrair_numero_estudante(email)
            if numero and (
                Perfil.objects.filter(numero_estudante=numero)
                .exclude(pk=self.pk)
                .exists()
            ):
                logger.warning(
                    "Número de estudante %s já atribuído a outro perfil "
                    "(user=%s); %s fica sem número.",
                    numero,
                    getattr(self.user, "email", ""),
                    self.pk,
                )
                numero = None
            self.numero_estudante = numero
            update_fields = kwargs.get("update_fields")
            if update_fields is not None and "numero_estudante" not in update_fields:
                kwargs["update_fields"] = [*update_fields, "numero_estudante"]
        super().save(*args, **kwargs)
