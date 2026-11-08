from decimal import Decimal
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, override_settings

from contas.models import Perfil
from pedidos.management.commands.seed_demo import PASSWORD_DEMO
from pedidos.models import TipoDocumento


@override_settings(
    IVA_PERCENT=Decimal("5"),
    TAXA_FORMULARIO=Decimal("20"),
)
class TipoDocumentoTaxasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def test_total_e_total_com_formulario_dos_sete_tipos(self):
        esperados = {
            "Declaração simples": (Decimal("105.00"), Decimal("126.00")),
            "Declaração de notas": (Decimal("210.00"), Decimal("231.00")),
            "Certificado normal": (Decimal("2625.00"), Decimal("2646.00")),
            "Certificado normal (2.ª via)": (
                Decimal("5250.00"),
                Decimal("5271.00"),
            ),
            "Certificado urgente": (Decimal("5250.00"), Decimal("5271.00")),
            "Diploma normal": (Decimal("2100.00"), Decimal("2121.00")),
            "Conteúdos programáticos": (Decimal("735.00"), Decimal("756.00")),
        }

        self.assertEqual(TipoDocumento.objects.count(), 7)

        for nome, (total, total_com_formulario) in esperados.items():
            with self.subTest(documento=nome):
                documento = TipoDocumento.objects.get(nome=nome)
                self.assertEqual(documento.total("licenciatura"), total)
                self.assertEqual(
                    documento.total_com_formulario("licenciatura"),
                    total_com_formulario,
                )

    def test_iva_usa_a_percentagem_configurada(self):
        documento = TipoDocumento.objects.get(nome="Certificado normal")
        self.assertEqual(documento.iva("licenciatura"), Decimal("125.00"))
        self.assertEqual(documento.taxa_base("licenciatura"), Decimal("2500.00"))

    def test_taxas_base_por_grau(self):
        documento = TipoDocumento.objects.get(nome="Certificado normal")
        self.assertEqual(documento.taxa_base("mestrado"), Decimal("5000.00"))
        self.assertEqual(
            documento.taxa_base("doutoramento"),
            Decimal("10000.00"),
        )


class SeedDemoTests(TestCase):
    def test_seed_demo_e_idempotente(self):
        call_command("seed_demo", stdout=StringIO())

        contagens_iniciais = (
            TipoDocumento.objects.count(),
            User.objects.count(),
            Perfil.objects.count(),
        )
        self.assertEqual(TipoDocumento.objects.count(), 7)

        call_command("seed_demo", stdout=StringIO())

        self.assertEqual(
            (
                TipoDocumento.objects.count(),
                User.objects.count(),
                Perfil.objects.count(),
            ),
            contagens_iniciais,
        )

    def test_seed_demo_cria_contas_e_dados_academicos(self):
        call_command("seed_demo", stdout=StringIO())

        papeis = {
            "admin": Perfil.PAPEL_ADMIN,
            "secretaria1": Perfil.PAPEL_SECRETARIA,
            "credito1": Perfil.PAPEL_CREDITO,
            "registo1": Perfil.PAPEL_REGISTO,
            "estudante1": Perfil.PAPEL_ESTUDANTE,
        }

        for username, papel in papeis.items():
            with self.subTest(username=username):
                utilizador = User.objects.get(username=username)
                self.assertEqual(utilizador.perfil.papel, papel)
                self.assertTrue(utilizador.check_password(PASSWORD_DEMO))

        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

        estudante = User.objects.get(username="estudante1")
        self.assertEqual(estudante.perfil.numero_estudante, "2023001234")
        self.assertEqual(estudante.perfil.curso, "Informática de Gestão")
        self.assertEqual(estudante.perfil.grau, Perfil.GRAU_LICENCIATURA)

    def test_seed_demo_cria_as_taxas_esperadas(self):
        call_command("seed_demo", stdout=StringIO())

        certificado = TipoDocumento.objects.get(nome="Certificado normal")
        self.assertEqual(certificado.taxa_licenciatura, Decimal("2500"))
        self.assertEqual(certificado.taxa_mestrado, Decimal("5000"))
        self.assertEqual(certificado.taxa_doutoramento, Decimal("10000"))
        self.assertTrue(certificado.passa_registo_academico)
        self.assertEqual(certificado.prazo_estimado_dias, 15)
        self.assertTrue(certificado.activo)

        declaracao = TipoDocumento.objects.get(nome="Declaração simples")
        self.assertFalse(declaracao.passa_registo_academico)
        self.assertIsNone(declaracao.prazo_estimado_dias)
