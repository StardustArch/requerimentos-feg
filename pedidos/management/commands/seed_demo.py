import os
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from contas.models import Perfil
from pedidos.models import TipoDocumento

PASSWORD_DEMO = os.environ.get("DEMO_PASSWORD", "demo123")

TIPOS_DOCUMENTO = (
    {
        "nome": "Declaração simples",
        "taxa_licenciatura": Decimal("100"),
        "taxa_mestrado": Decimal("200"),
        "taxa_doutoramento": Decimal("300"),
        "passa_registo_academico": False,
        "prazo_estimado_dias": None,
    },
    {
        "nome": "Declaração de notas",
        "taxa_licenciatura": Decimal("200"),
        "taxa_mestrado": Decimal("300"),
        "taxa_doutoramento": Decimal("400"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": None,
    },
    {
        "nome": "Certificado normal",
        "taxa_licenciatura": Decimal("2500"),
        "taxa_mestrado": Decimal("5000"),
        "taxa_doutoramento": Decimal("10000"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": 15,
    },
    {
        "nome": "Certificado normal (2.ª via)",
        "taxa_licenciatura": Decimal("5000"),
        "taxa_mestrado": Decimal("7500"),
        "taxa_doutoramento": Decimal("12500"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": 15,
    },
    {
        "nome": "Certificado urgente",
        "taxa_licenciatura": Decimal("5000"),
        "taxa_mestrado": Decimal("10000"),
        "taxa_doutoramento": Decimal("20000"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": 5,
    },
    {
        "nome": "Diploma normal",
        "taxa_licenciatura": Decimal("2000"),
        "taxa_mestrado": Decimal("3000"),
        "taxa_doutoramento": Decimal("10000"),
        "passa_registo_academico": False,
        "prazo_estimado_dias": 15,
    },
    {
        "nome": "Conteúdos programáticos",
        "taxa_licenciatura": Decimal("700"),
        "taxa_mestrado": Decimal("1400"),
        "taxa_doutoramento": Decimal("2100"),
        "passa_registo_academico": False,
        "prazo_estimado_dias": None,
    },
)

UTILIZADORES_DEMO = (
    {
        "username": "admin",
        "email": "admin@ucm.ac.mz",
        "papel": Perfil.PAPEL_ADMIN,
        "superuser": True,
    },
    {
        "username": "secretaria1",
        "email": "secretaria1@ucm.ac.mz",
        "papel": Perfil.PAPEL_SECRETARIA,
        "superuser": False,
    },
    {
        "username": "credito1",
        "email": "credito1@ucm.ac.mz",
        "papel": Perfil.PAPEL_CREDITO,
        "superuser": False,
    },
    {
        "username": "registo1",
        "email": "registo1@ucm.ac.mz",
        "papel": Perfil.PAPEL_REGISTO,
        "superuser": False,
    },
    {
        "username": "estudante1",
        "email": "estudante1@estudante.ucm.ac.mz",
        "papel": Perfil.PAPEL_ESTUDANTE,
        "superuser": False,
        "numero_estudante": "2023001234",
        "curso": "Informática de Gestão",
        "grau": Perfil.GRAU_LICENCIATURA,
    },
)


class Command(BaseCommand):
    help = "Cria os tipos de documento e as contas de demonstração."

    def handle(self, *args, **options):
        tipos_criados = 0
        tipos_existentes = 0
        utilizadores_criados = 0
        utilizadores_existentes = 0

        for dados in TIPOS_DOCUMENTO:
            _, criado = TipoDocumento.objects.update_or_create(
                nome=dados["nome"],
                defaults={
                    "taxa_licenciatura": dados["taxa_licenciatura"],
                    "taxa_mestrado": dados["taxa_mestrado"],
                    "taxa_doutoramento": dados["taxa_doutoramento"],
                    "passa_registo_academico": dados["passa_registo_academico"],
                    "prazo_estimado_dias": dados["prazo_estimado_dias"],
                    "activo": True,
                },
            )
            if criado:
                tipos_criados += 1
            else:
                tipos_existentes += 1

        for dados in UTILIZADORES_DEMO:
            _, criado = self._garantir_utilizador(dados)
            if criado:
                utilizadores_criados += 1
            else:
                utilizadores_existentes += 1

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(
            "Tipos de documento: {criados} criados, {existentes} já existiam".format(
                criados=tipos_criados,
                existentes=tipos_existentes,
            )
        )
        self.stdout.write(
            "Utilizadores: {criados} criados, {existentes} já existiam".format(
                criados=utilizadores_criados,
                existentes=utilizadores_existentes,
            )
        )

        if PASSWORD_DEMO == "demo123":
            self.stdout.write(
                self.style.WARNING(
                    "AVISO: a palavra-passe de demonstração está a usar o valor "
                    "por defeito (demo123). Defina a variável de ambiente "
                    "DEMO_PASSWORD em produção."
                )
            )

    def _garantir_utilizador(self, dados):
        utilizador, criado = User.objects.get_or_create(
            username=dados["username"],
            defaults={
                "email": dados["email"],
                "is_staff": dados["superuser"],
                "is_superuser": dados["superuser"],
            },
        )

        alterado = False
        if criado:
            utilizador.set_password(PASSWORD_DEMO)
            alterado = True

        if not utilizador.email:
            utilizador.email = dados["email"]
            alterado = True

        if dados["superuser"] and (
            not utilizador.is_staff or not utilizador.is_superuser
        ):
            utilizador.is_staff = True
            utilizador.is_superuser = True
            alterado = True

        if alterado:
            utilizador.save()

        perfil, _ = Perfil.objects.get_or_create(user=utilizador)
        campos_alterados = []

        if perfil.papel != dados["papel"]:
            perfil.papel = dados["papel"]
            campos_alterados.append("papel")

        for campo in ("numero_estudante", "curso", "grau"):
            valor = dados.get(campo)
            if valor and not getattr(perfil, campo):
                setattr(perfil, campo, valor)
                campos_alterados.append(campo)

        if campos_alterados:
            perfil.save(update_fields=campos_alterados)

        return utilizador, criado
