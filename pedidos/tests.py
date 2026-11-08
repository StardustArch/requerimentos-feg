import shutil
import tempfile
from decimal import Decimal
from io import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve, reverse

from contas.models import Perfil
from pedidos.management.commands.seed_demo import PASSWORD_DEMO, PNG_MINIMO
from pedidos.models import Anexo, Pedido, TipoDocumento
from pedidos.validators import validar_anexo


class MediaTempMixin:
    """Garante que os ficheiros dos testes não ficam em media/."""

    @classmethod
    def setUpClass(cls):
        cls._media_temp = tempfile.mkdtemp(prefix="requerimentos-test-media-")
        cls.enterClassContext(override_settings(MEDIA_ROOT=cls._media_temp))
        cls.addClassCleanup(shutil.rmtree, cls._media_temp, ignore_errors=True)
        super().setUpClass()


@override_settings(
    IVA_PERCENT=Decimal("5"),
    TAXA_FORMULARIO=Decimal("20"),
)
class TipoDocumentoTaxasTests(MediaTempMixin, TestCase):
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


class SeedDemoTests(MediaTempMixin, TestCase):
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

    def test_seed_demo_cria_tres_pedidos_com_dois_anexos_cada(self):
        call_command("seed_demo", stdout=StringIO())

        estudante = User.objects.get(username="estudante1")
        pedidos = Pedido.objects.filter(estudante=estudante)
        self.assertEqual(pedidos.count(), 3)
        self.assertEqual(Anexo.objects.filter(pedido__in=pedidos).count(), 6)

        etapas = set(pedidos.values_list("etapa_actual", flat=True))
        self.assertIn(Pedido.ETAPA_SECRETARIA_RECEPCAO, etapas)
        self.assertIn(Pedido.ETAPA_CREDITO, etapas)

        indeferido = pedidos.get(estado=Pedido.ESTADO_INDEFERIDO)
        self.assertTrue(indeferido.motivo_indeferimento)

        for pedido in pedidos:
            with self.subTest(protocolo=pedido.protocolo):
                self.assertRegex(pedido.protocolo, r"^REQ-\d{4}-\d{5}$")
                self.assertEqual(pedido.anexos.count(), 2)
                extensoes = {
                    anexo.ficheiro.name.rsplit(".", 1)[-1].lower()
                    for anexo in pedido.anexos.all()
                }
                self.assertEqual(extensoes, {"pdf", "png"})

        call_command("seed_demo", stdout=StringIO())
        self.assertEqual(pedidos.count(), 3)
        self.assertEqual(Anexo.objects.filter(pedido__in=pedidos).count(), 6)


def ficheiro_pdf(nome="bi.pdf", conteudo=None):
    return SimpleUploadedFile(
        nome,
        conteudo or b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n",
        content_type="application/pdf",
    )


def ficheiro_png(nome="comprovativo.png"):
    return SimpleUploadedFile(nome, PNG_MINIMO, content_type="image/png")


class PedidoEstudanteTests(MediaTempMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def setUp(self):
        self.estudante = User.objects.get(username="estudante1")
        self.tipo = TipoDocumento.objects.get(nome="Certificado normal")
        self.client.force_login(self.estudante)

    def _submeter(self, **alteracoes):
        dados = {
            "tipo": self.tipo.pk,
            "motivo": "Preciso do documento para apresentar numa instituição.",
            "anexo_bi": ficheiro_pdf(),
            "anexo_comprovativo": ficheiro_png(),
        }
        dados.update(alteracoes)
        return self.client.post(reverse("pedidos:novo_pedido"), dados)

    def test_submissao_valida_cria_pedido_protocolo_e_dois_anexos(self):
        antes = Pedido.objects.count()
        motivo = "Pedido válido para o teste de submissão."

        resposta = self._submeter(motivo=motivo)

        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(Pedido.objects.count(), antes + 1)

        pedido = Pedido.objects.get(motivo=motivo)
        self.assertRegex(pedido.protocolo, r"^REQ-\d{4}-\d{5}$")
        self.assertEqual(pedido.protocolo, f"REQ-{pedido.criado_em.year}-{pedido.pk:05d}")
        self.assertEqual(pedido.estado, Pedido.ESTADO_EM_TRATAMENTO)
        self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_SECRETARIA_RECEPCAO)
        self.assertEqual(pedido.grau, self.estudante.perfil.grau)
        self.assertEqual(
            pedido.valor_total,
            self.tipo.total_com_formulario(self.estudante.perfil.grau),
        )
        self.assertEqual(pedido.anexos.count(), 2)
        self.assertEqual(
            set(pedido.anexos.values_list("tipo", flat=True)),
            {Anexo.TIPO_BI, Anexo.TIPO_COMPROVATIVO},
        )

        for anexo in pedido.anexos.all():
            self.assertTrue(anexo.visivel_ao_estudante)
            self.assertEqual(anexo.carregado_por, self.estudante)
            self.assertTrue(anexo.ficheiro.name.startswith("pedidos/"))
            self.assertEqual(
                anexo.ficheiro.name,
                f"pedidos/{pedido.criado_em.year}/"
                f"{anexo.ficheiro.name.rsplit('/', 1)[-1]}",
            )
            nome_guardado = anexo.ficheiro.name.rsplit("/", 1)[-1]
            self.assertNotEqual(nome_guardado, anexo.nome_original)
            self.assertRegex(
                nome_guardado,
                r"^[0-9a-f]{32}\.(pdf|png)$",
            )

        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[pedido.pk])
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, pedido.protocolo)
        self.assertContains(resposta, pedido.tipo.nome)

    def test_anexos_invalidos_sao_rejeitados_sem_criar_nada(self):
        casos = (
            (
                "extensão não permitida",
                {"anexo_bi": SimpleUploadedFile("bi.txt", b"%PDF-1.4\n")},
                "Formato não permitido",
            ),
            (
                "conteúdo falso com extensão pdf",
                {
                    "anexo_bi": SimpleUploadedFile(
                        "bi.pdf",
                        b"isto e apenas texto, nao e um PDF",
                    )
                },
                "não corresponde",
            ),
        )

        for nome, alteracoes, mensagem in casos:
            with self.subTest(caso=nome):
                antes = Pedido.objects.count()
                resposta = self._submeter(**alteracoes)
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(Pedido.objects.count(), antes)
                self.assertIn(mensagem, str(resposta.context["form"].errors))

        with override_settings(MAX_ANEXO_MB=1):
            antes = Pedido.objects.count()
            grande = b"%PDF-1.4\n" + (b"x" * (1024 * 1024))
            resposta = self._submeter(
                anexo_bi=SimpleUploadedFile("grande.pdf", grande)
            )
            self.assertEqual(resposta.status_code, 200)
            self.assertEqual(Pedido.objects.count(), antes)
            self.assertIn("excede o limite", str(resposta.context["form"].errors))

    def test_falta_de_um_dos_anexos_obrigatorios_e_rejeitada(self):
        for campo_em_falta in ("anexo_bi", "anexo_comprovativo"):
            with self.subTest(campo=campo_em_falta):
                dados = {
                    "tipo": self.tipo.pk,
                    "motivo": "Pedido sem um dos anexos obrigatórios.",
                }
                if campo_em_falta != "anexo_bi":
                    dados["anexo_bi"] = ficheiro_pdf()
                if campo_em_falta != "anexo_comprovativo":
                    dados["anexo_comprovativo"] = ficheiro_png()

                antes = Pedido.objects.count()
                resposta = self.client.post(
                    reverse("pedidos:novo_pedido"),
                    dados,
                )

                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(Pedido.objects.count(), antes)
                self.assertIn(
                    campo_em_falta,
                    resposta.context["form"].errors,
                )

    def test_tipo_inactivo_nao_aparece_nem_e_aceite(self):
        inactivo = TipoDocumento.objects.get(nome="Conteúdos programáticos")
        inactivo.activo = False
        inactivo.save(update_fields=["activo"])

        resposta = self.client.get(reverse("pedidos:novo_pedido"))
        self.assertEqual(resposta.status_code, 200)
        self.assertNotContains(resposta, inactivo.nome)
        self.assertContains(resposta, 'vendor/htmx/htmx.min.js')

        antes = Pedido.objects.count()
        resposta = self._submeter(tipo=inactivo.pk)

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Pedido.objects.count(), antes)
        self.assertIn("tipo", resposta.context["form"].errors)

    def test_estudante_sem_perfil_completo_e_redireccionado(self):
        incompleto = User.objects.create_user(
            username="estudante_incompleto_pedidos",
            password="teste12345",
        )
        perfil = incompleto.perfil
        perfil.grau = ""
        perfil.curso = ""
        perfil.save(update_fields=["grau", "curso"])

        self.client.force_login(incompleto)
        antes = Pedido.objects.count()

        resposta = self._submeter(motivo="Não deve ser criado.")

        self.assertRedirects(
            resposta,
            reverse("contas:completar_perfil"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Pedido.objects.count(), antes)

    def test_outro_estudante_recebe_404_no_detalhe_e_no_anexo(self):
        outro = User.objects.create_user(
            username="outro_estudante_pedidos",
            password="teste12345",
        )
        perfil = outro.perfil
        perfil.grau = Perfil.GRAU_LICENCIATURA
        perfil.curso = "Gestão"
        perfil.save(update_fields=["grau", "curso"])

        pedido = Pedido.objects.filter(estudante=self.estudante).first()
        anexo = pedido.anexos.first()
        self.client.force_login(outro)

        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[pedido.pk])
        )
        self.assertEqual(resposta.status_code, 404)

        resposta = self.client.get(
            reverse("pedidos:anexo_download", args=[anexo.pk])
        )
        self.assertEqual(resposta.status_code, 404)

    def test_dono_descarrega_anexos_visiveis_e_nao_os_ocultos(self):
        pedido = Pedido.objects.filter(estudante=self.estudante).first()
        tipos_esperados = {
            Anexo.TIPO_BI: "application/pdf",
            Anexo.TIPO_COMPROVATIVO: "image/png",
        }

        for anexo in pedido.anexos.all():
            with self.subTest(tipo=anexo.tipo):
                resposta = self.client.get(
                    reverse("pedidos:anexo_download", args=[anexo.pk])
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(
                    resposta["Content-Type"],
                    tipos_esperados[anexo.tipo],
                )
                self.assertIn("attachment", resposta["Content-Disposition"].lower())
                self.assertIn(
                    anexo.nome_original,
                    resposta["Content-Disposition"],
                )
                self.assertEqual(
                    resposta["X-Content-Type-Options"],
                    "nosniff",
                )

        oculto = Anexo.objects.create(
            pedido=pedido,
            tipo=Anexo.TIPO_OUTRO,
            ficheiro=ficheiro_pdf("oculto.pdf"),
            nome_original="oculto.pdf",
            visivel_ao_estudante=False,
            carregado_por=self.estudante,
        )
        resposta = self.client.get(
            reverse("pedidos:anexo_download", args=[oculto.pk])
        )
        self.assertEqual(resposta.status_code, 404)

        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[pedido.pk])
        )
        self.assertNotContains(resposta, "oculto.pdf")

    def test_utilizador_sem_sessao_e_redireccionado_para_o_login(self):
        pedido = Pedido.objects.filter(estudante=self.estudante).first()
        anexo = pedido.anexos.first()
        self.client.logout()

        url = reverse("pedidos:meus_pedidos")
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 302)
        self.assertEqual(
            resposta.url,
            f"{settings.LOGIN_URL}?next={url}",
        )

        resposta = self.client.get(
            reverse("pedidos:anexo_download", args=[anexo.pk])
        )
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(settings.LOGIN_URL))

    def test_valor_total_fica_congelado_quando_a_taxa_muda(self):
        pedido = Pedido.objects.create(
            estudante=self.estudante,
            tipo=self.tipo,
            grau=self.estudante.perfil.grau,
            motivo="Pedido para testar o congelamento da taxa.",
        )
        valor_inicial = pedido.valor_total

        self.tipo.taxa_licenciatura = Decimal("999999")
        self.tipo.taxa_mestrado = Decimal("999999")
        self.tipo.taxa_doutoramento = Decimal("999999")
        self.tipo.save(
            update_fields=[
                "taxa_licenciatura",
                "taxa_mestrado",
                "taxa_doutoramento",
            ]
        )

        pedido.refresh_from_db()
        self.assertEqual(pedido.valor_total, valor_inicial)
        self.assertNotEqual(
            pedido.valor_total,
            self.tipo.total_com_formulario(self.estudante.perfil.grau),
        )

    def test_endpoint_htmx_devolve_a_taxa_certa_para_cada_grau(self):
        url = reverse("pedidos:resumo_pedido")
        graus = (
            Perfil.GRAU_LICENCIATURA,
            Perfil.GRAU_MESTRADO,
            Perfil.GRAU_DOUTORAMENTO,
        )

        for grau in graus:
            with self.subTest(grau=grau):
                perfil = self.estudante.perfil
                perfil.grau = grau
                perfil.save(update_fields=["grau"])

                resposta = self.client.get(url, {"tipo": self.tipo.pk})

                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(
                    resposta.context["total"],
                    self.tipo.total_com_formulario(grau),
                )
                self.assertEqual(
                    resposta.context["prazo_estimado_dias"],
                    self.tipo.prazo_estimado_dias,
                )
                self.assertContains(resposta, self.tipo.nome)
                self.assertContains(resposta, "dias úteis")

    def test_meus_pedidos_ordena_do_mais_recente_para_o_mais_antigo(self):
        resposta = self.client.get(reverse("pedidos:meus_pedidos"))
        self.assertEqual(resposta.status_code, 200)

        pedidos = list(resposta.context["pedidos"])
        self.assertGreaterEqual(len(pedidos), 3)
        self.assertEqual(
            pedidos,
            sorted(pedidos, key=lambda pedido: pedido.criado_em, reverse=True),
        )
        for pedido in pedidos:
            self.assertEqual(pedido.estudante, self.estudante)

    def test_nenhuma_rota_serve_a_pasta_media(self):
        self.assertFalse(
            getattr(settings, "MEDIA_URL", "").startswith("/media")
        )

        for caminho in (
            "/media/",
            "/media/pedidos/2026/ficheiro.pdf",
            f"{settings.MEDIA_ROOT}/pedidos/2026/ficheiro.pdf",
        ):
            with self.subTest(caminho=caminho):
                with self.assertRaises(Resolver404):
                    resolve(caminho)


class AnexoDownloadStaffTests(MediaTempMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def setUp(self):
        self.estudante = User.objects.get(username="estudante1")
        self.tipo = TipoDocumento.objects.get(nome="Declaração simples")
        self.anexos = {}

        for etapa in (
            Pedido.ETAPA_SECRETARIA_RECEPCAO,
            Pedido.ETAPA_CREDITO,
            Pedido.ETAPA_REGISTO,
            Pedido.ETAPA_SECRETARIA_FINAL,
        ):
            pedido = Pedido.objects.create(
                estudante=self.estudante,
                tipo=self.tipo,
                grau=self.estudante.perfil.grau,
                motivo=f"Pedido de teste para a etapa {etapa}.",
                etapa_actual=etapa,
            )
            self.anexos[etapa] = Anexo.objects.create(
                pedido=pedido,
                tipo=Anexo.TIPO_BI,
                ficheiro=ficheiro_pdf(f"bi_{etapa}.pdf"),
                nome_original=f"bi_{etapa}.pdf",
                visivel_ao_estudante=True,
                carregado_por=self.estudante,
            )

    def _verificar(self, username, permitidas):
        utilizador = User.objects.get(username=username)
        self.client.force_login(utilizador)

        for etapa, anexo in self.anexos.items():
            with self.subTest(utilizador=username, etapa=etapa):
                resposta = self.client.get(
                    reverse("pedidos:anexo_download", args=[anexo.pk])
                )
                esperado = 200 if etapa in permitidas else 404
                self.assertEqual(resposta.status_code, esperado)

    def test_credito_so_descarrega_na_etapa_credito(self):
        self._verificar("credito1", {Pedido.ETAPA_CREDITO})

    def test_registo_so_descarrega_na_etapa_registo(self):
        self._verificar("registo1", {Pedido.ETAPA_REGISTO})

    def test_secretaria_e_admin_descarregam_sempre(self):
        todas = set(self.anexos)
        self._verificar("secretaria1", todas)
        self._verificar("admin", todas)


@override_settings(
    IVA_PERCENT=Decimal("5"),
    TAXA_FORMULARIO=Decimal("20"),
)
class ValidacaoAnexosTests(TestCase):
    def test_aceita_assinaturas_correspondentes(self):
        ficheiros = (
            ficheiro_pdf("documento.pdf"),
            ficheiro_png("imagem.png"),
            SimpleUploadedFile("foto.jpg", b"\xff\xd8\xff\xe0" + b"conteudo"),
            SimpleUploadedFile("foto.jpeg", b"\xff\xd8\xff\xe0" + b"conteudo"),
        )

        for ficheiro in ficheiros:
            with self.subTest(ficheiro=ficheiro.name):
                validar_anexo(ficheiro)

    def test_rejeita_assinatura_que_nao_bate_com_a_extensao(self):
        casos = (
            SimpleUploadedFile("falso.pdf", b"\x89PNG\r\n\x1a\n"),
            SimpleUploadedFile("falso.png", b"%PDF-1.4\n"),
            SimpleUploadedFile("falso.jpg", b"texto qualquer"),
        )

        for ficheiro in casos:
            with self.subTest(ficheiro=ficheiro.name):
                with self.assertRaises(ValidationError):
                    validar_anexo(ficheiro)
