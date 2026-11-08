from django.contrib.auth.models import User
from django.db import models


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
    numero_estudante = models.CharField(
        max_length=30, blank=True, null=True
    )
    curso = models.CharField(max_length=150, blank=True, null=True)
    grau = models.CharField(
        max_length=20, choices=GRAU_CHOICES, blank=True, null=True
    )
    telefone = models.CharField(max_length=20, blank=True, null=True)

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
        return bool(self.grau and self.curso)
