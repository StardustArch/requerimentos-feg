import shutil
import tempfile
import uuid
from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contas.models import Perfil
from pedidos import services
from pedidos.management.commands.seed_demo import PNG_MINIMO
from pedidos.models import Anexo, Decisao, Pedido, TipoDocumento


class MediaTempMixin:
    @classmethod
    def setUpClass(cls):
        cls._media_temp = tempfile.mkdtemp(prefix="requerimentos-fase3-media-")
        cls.enterClassContext(override_settings(MEDIA_ROOT=cls._media_temp))
        cls.addClassCleanup(shutil.rmtree, cls._media_temp, ignore_errors=True)
        super().setUpClass()


def ficheiro_pdf(nome="documento.pdf"):
    return SimpleUploadedFile(
        nome,
        b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n",
        content_type="application/pdf",
    )


def ficheiro_png(nome="imagem.png"):
    return SimpleUploadedFile(nome, PNG_MINIMO, content_type="image/png")


class Fase3Base(MediaTempMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=StringIO())

    def setUp(self):
        self.estudante = User.objects.get(username="estudante1")
        self.secretaria = User.objects.get(username="secretaria1")
        self.credito = User.objects.get(username="credito1")
        self.registo = User.objects.get(username="registo1")
        self.admin = User.objects.get(username="admin")
        self.tipo_sem_registo = TipoDocumento.objects.get(
            nome="Declaração simples"
        )
        self.tipo_com_registo = TipoDocumento.objects.get(
            nome="Declaração de notas"
        )

    def criar_pedido(self, tipo=None, etapa=None, estado=None):
        return Pedido.objects.create(
            estudante=self.estudante,
            tipo=tipo or self.tipo_sem_registo,
            grau=self.estudante.perfil.grau,
            motivo=f"Pedido de teste {uuid.uuid4().hex}",
            etapa_actual=etapa or Pedido.ETAPA_SECRETARIA_RECEPCAO,
            estado=estado or Pedido.ESTADO_EM_TRATAMENTO,
        )


class RotaEServicosTests(Fase3Base):
    def test_rota_completa_sem_registo(self):
        pedido = self.criar_pedido(self.tipo_sem_registo)

        pedido = services.aprovar(pedido, self.secretaria, "Recepção ok")
        self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_CREDITO)

        pedido = services.aprovar(pedido, self.credito, "Pagamento ok")
        self.assertEqual(
            pedido.etapa_actual,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )

        pedido = services.marcar_pronto(pedido, self.secretaria)
        self.assertEqual(pedido.estado, Pedido.ESTADO_PRONTO)
        self.assertIsNotNone(pedido.pronto_em)

        pedido = services.marcar_entregue(pedido, self.secretaria)
        self.assertEqual(pedido.estado, Pedido.ESTADO_ENTREGUE)
        self.assertIsNotNone(pedido.entregue_em)
        self.assertEqual(pedido.entregue_por, self.secretaria)

        self.assertEqual(
            list(
                pedido.decisoes.values_list("etapa", "resultado")
            ),
            [
                (
                    Pedido.ETAPA_SECRETARIA_RECEPCAO,
                    Decisao.RESULTADO_APROVADO,
                ),
                (Pedido.ETAPA_CREDITO, Decisao.RESULTADO_APROVADO),
                (Pedido.ETAPA_SECRETARIA_FINAL, Decisao.RESULTADO_PRONTO),
                (Pedido.ETAPA_SECRETARIA_FINAL, Decisao.RESULTADO_ENTREGUE),
            ],
        )

    def test_rota_com_tipo_que_passa_pelo_registo(self):
        pedido = self.criar_pedido(self.tipo_com_registo)

        pedido = services.aprovar(pedido, self.secretaria)
        pedido = services.aprovar(pedido, self.credito)
        self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_REGISTO)

        pedido = services.aprovar(pedido, self.registo)
        self.assertEqual(
            pedido.etapa_actual,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )

        pedido = services.marcar_pronto(pedido, self.secretaria)
        self.assertEqual(pedido.estado, Pedido.ESTADO_PRONTO)
        self.assertEqual(
            pedido.decisoes.filter(
                etapa=Pedido.ETAPA_REGISTO,
                resultado=Decisao.RESULTADO_APROVADO,
            ).count(),
            1,
        )

    def test_cada_papel_so_aprova_na_sua_etapa(self):
        casos = (
            (
                Pedido.ETAPA_SECRETARIA_RECEPCAO,
                self.secretaria,
                (self.credito, self.registo),
            ),
            (
                Pedido.ETAPA_CREDITO,
                self.credito,
                (self.secretaria, self.registo),
            ),
            (
                Pedido.ETAPA_REGISTO,
                self.registo,
                (self.secretaria, self.credito),
            ),
        )

        for etapa, actor_certo, actores_errados in casos:
            with self.subTest(etapa=etapa):
                pedido = self.criar_pedido(etapa=etapa)
                for actor in actores_errados:
                    with self.assertRaises(PermissionDenied):
                        services.aprovar(pedido, actor)
                self.assertFalse(pedido.decisoes.exists())

                services.aprovar(pedido, actor_certo)
                self.assertEqual(pedido.decisoes.count(), 1)

    def test_admin_pode_decidir_em_qualquer_etapa(self):
        pedido = self.criar_pedido(
            self.tipo_sem_registo,
            etapa=Pedido.ETAPA_SECRETARIA_RECEPCAO,
        )
        pedido = services.aprovar(pedido, self.admin)
        self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_CREDITO)

        pedido = services.aprovar(pedido, self.admin)
        self.assertEqual(
            pedido.etapa_actual,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )

        pedido = services.marcar_pronto(pedido, self.admin)
        self.assertEqual(pedido.estado, Pedido.ESTADO_PRONTO)

        pedido = self.criar_pedido(etapa=Pedido.ETAPA_REGISTO)
        pedido = services.aprovar(pedido, self.admin)
        self.assertEqual(
            pedido.etapa_actual,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )

    def test_vista_de_aprovacao_devolve_403_ao_papel_errado(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_SECRETARIA_RECEPCAO)
        url = reverse("pedidos:aprovar", args=[pedido.pk])

        self.client.force_login(self.credito)
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 403)
        pedido.refresh_from_db()
        self.assertEqual(
            pedido.etapa_actual,
            Pedido.ETAPA_SECRETARIA_RECEPCAO,
        )

        self.client.force_login(self.admin)
        resposta = self.client.post(url)
        self.assertEqual(resposta.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_CREDITO)

    def test_indeferir_exige_motivo_com_pelo_menos_dez_caracteres(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)

        for motivo in ("", "   ", "curto"):
            with self.subTest(motivo=motivo):
                with self.assertRaises(ValidationError):
                    services.indeferir(pedido, self.credito, motivo)

        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.ESTADO_EM_TRATAMENTO)
        self.assertFalse(pedido.decisoes.exists())

    def test_indeferir_para_o_pedido_e_guarda_motivo_e_etapa(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        motivo = "O comprovativo não corresponde ao valor esperado."

        pedido = services.indeferir(pedido, self.credito, motivo)

        self.assertEqual(pedido.estado, Pedido.ESTADO_INDEFERIDO)
        self.assertEqual(pedido.motivo_indeferimento, motivo)
        self.assertEqual(
            pedido.indeferido_na_etapa,
            Pedido.ETAPA_CREDITO,
        )
        self.assertEqual(
            pedido.decisoes.get().resultado,
            Decisao.RESULTADO_INDEFERIDO,
        )

        with self.assertRaises(ValidationError):
            services.aprovar(pedido, self.admin)
        self.assertEqual(pedido.decisoes.count(), 1)

    def test_aprovar_pedido_ja_decidido_ou_na_etapa_errada_falha(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        with self.assertRaises(PermissionDenied):
            services.aprovar(pedido, self.secretaria)
        self.assertFalse(pedido.decisoes.exists())

        pedido = self.criar_pedido(etapa=Pedido.ETAPA_SECRETARIA_FINAL)
        pedido = services.marcar_pronto(pedido, self.secretaria)
        decisoes_antes = pedido.decisoes.count()

        with self.assertRaises(ValidationError):
            services.aprovar(pedido, self.admin)

        self.assertEqual(pedido.decisoes.count(), decisoes_antes)

    def test_decisao_e_imutavel(self):
        pedido = self.criar_pedido()
        decisao = Decisao.objects.create(
            pedido=pedido,
            etapa=Pedido.ETAPA_SECRETARIA_RECEPCAO,
            resultado=Decisao.RESULTADO_APROVADO,
            decidido_por=self.secretaria,
        )

        decisao.justificacao = "Tentativa de alteração."
        with self.assertRaises(ValidationError):
            decisao.save()
        with self.assertRaises(ValidationError):
            decisao.delete()

        decisao.refresh_from_db()
        self.assertEqual(decisao.justificacao, "")


class EmailTests(Fase3Base):
    @override_settings(LEVANTAMENTO_INFO="no balcão 3 da Secretaria")
    def test_email_de_pronto_inclui_protocolo_e_local_de_levantamento(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_SECRETARIA_FINAL)

        with self.captureOnCommitCallbacks(execute=True):
            pedido = services.marcar_pronto(pedido, self.secretaria)

        self.assertEqual(len(mail.outbox), 1)
        mensagem = mail.outbox[0]
        self.assertEqual(mensagem.to, [self.estudante.email])
        self.assertIn(pedido.protocolo, mensagem.subject)
        self.assertIn(pedido.protocolo, mensagem.body)
        self.assertIn(pedido.tipo.nome, mensagem.body)
        self.assertIn("no balcão 3 da Secretaria", mensagem.body)

    def test_email_de_indeferido_inclui_protocolo_e_motivo(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        motivo = "O valor pago é inferior ao valor esperado."

        with self.captureOnCommitCallbacks(execute=True):
            pedido = services.indeferir(pedido, self.credito, motivo)

        self.assertEqual(len(mail.outbox), 1)
        mensagem = mail.outbox[0]
        self.assertEqual(mensagem.to, [self.estudante.email])
        self.assertIn(pedido.protocolo, mensagem.subject)
        self.assertIn(motivo, mensagem.body)

    def test_falha_de_envio_nao_impede_a_decisao(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_SECRETARIA_FINAL)

        with patch(
            "pedidos.notificacoes.send_mail",
            side_effect=RuntimeError("servidor de email indisponível"),
        ):
            with self.assertLogs("pedidos.notificacoes", level="ERROR"):
                with self.captureOnCommitCallbacks(execute=True):
                    pedido = services.marcar_pronto(pedido, self.secretaria)

        self.assertEqual(pedido.estado, Pedido.ESTADO_PRONTO)
        self.assertEqual(len(mail.outbox), 0)

    def test_estudante_sem_email_nao_recebe_notificacao(self):
        self.estudante.email = ""
        self.estudante.save(update_fields=["email"])
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_SECRETARIA_FINAL)

        with self.captureOnCommitCallbacks(execute=True):
            services.marcar_pronto(pedido, self.secretaria)

        self.assertEqual(len(mail.outbox), 0)


class DetalheStaffEAnexosTests(Fase3Base):
    def test_credito_e_registo_so_veem_pedidos_da_sua_etapa(self):
        pedido_credito = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        pedido_registo = self.criar_pedido(etapa=Pedido.ETAPA_REGISTO)

        self.client.force_login(self.credito)
        self.assertEqual(
            self.client.get(
                reverse(
                    "pedidos:pedido_staff_detalhe",
                    args=[pedido_credito.pk],
                )
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "pedidos:pedido_staff_detalhe",
                    args=[pedido_registo.pk],
                )
            ).status_code,
            404,
        )

        self.client.force_login(self.registo)
        self.assertEqual(
            self.client.get(
                reverse(
                    "pedidos:pedido_staff_detalhe",
                    args=[pedido_credito.pk],
                )
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "pedidos:pedido_staff_detalhe",
                    args=[pedido_registo.pk],
                )
            ).status_code,
            200,
        )

        self.client.force_login(self.secretaria)
        for pedido in (pedido_credito, pedido_registo):
            with self.subTest(pedido=pedido.pk):
                self.assertEqual(
                    self.client.get(
                        reverse(
                            "pedidos:pedido_staff_detalhe",
                            args=[pedido.pk],
                        )
                    ).status_code,
                    200,
                )

    def test_carregar_extracto_e_privado_do_estudante_e_da_secretaria(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        url_upload = reverse(
            "pedidos:carregar_extracto",
            args=[pedido.pk],
        )

        self.client.force_login(self.credito)
        resposta = self.client.post(
            url_upload,
            {"ficheiro": ficheiro_pdf("extracto.pdf")},
        )
        self.assertEqual(resposta.status_code, 302)

        extracto = Anexo.objects.get(pedido=pedido, tipo=Anexo.TIPO_EXTRACTO)
        self.assertFalse(extracto.visivel_ao_estudante)
        self.assertEqual(extracto.carregado_por, self.credito)

        url_download = reverse(
            "pedidos:anexo_download",
            args=[extracto.pk],
        )
        self.assertEqual(
            self.client.get(url_download).status_code,
            200,
        )

        self.client.force_login(self.estudante)
        self.assertEqual(
            self.client.get(url_download).status_code,
            404,
        )
        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[pedido.pk])
        )
        self.assertNotContains(resposta, "extracto.pdf")

        for utilizador in (self.secretaria, self.registo):
            with self.subTest(utilizador=utilizador.username):
                self.client.force_login(utilizador)
                self.assertEqual(
                    self.client.get(url_download).status_code,
                    404,
                )

        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.get(url_download).status_code,
            200,
        )

    def test_carregar_extracto_rejeita_papel_ou_etapa_errada(self):
        pedido_credito = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        pedido_registo = self.criar_pedido(etapa=Pedido.ETAPA_REGISTO)
        url_credito = reverse(
            "pedidos:carregar_extracto",
            args=[pedido_credito.pk],
        )
        url_registo = reverse(
            "pedidos:carregar_extracto",
            args=[pedido_registo.pk],
        )

        for utilizador in (self.secretaria, self.registo):
            with self.subTest(utilizador=utilizador.username):
                self.client.force_login(utilizador)
                self.assertEqual(
                    self.client.post(
                        url_credito,
                        {"ficheiro": ficheiro_pdf("extracto.pdf")},
                    ).status_code,
                    403,
                )

        self.client.force_login(self.credito)
        self.assertEqual(
            self.client.post(
                url_registo,
                {"ficheiro": ficheiro_pdf("extracto.pdf")},
            ).status_code,
            404,
        )
        self.assertFalse(
            Anexo.objects.filter(
                pedido__in=(pedido_credito, pedido_registo),
                tipo=Anexo.TIPO_EXTRACTO,
            ).exists()
        )

    def test_extracto_com_ficheiro_invalido_nao_e_criado(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        self.client.force_login(self.credito)

        resposta = self.client.post(
            reverse("pedidos:carregar_extracto", args=[pedido.pk]),
            {
                "ficheiro": SimpleUploadedFile(
                    "extracto.txt",
                    b"isto nao e um ficheiro permitido",
                )
            },
        )

        self.assertEqual(resposta.status_code, 302)
        self.assertFalse(
            Anexo.objects.filter(
                pedido=pedido,
                tipo=Anexo.TIPO_EXTRACTO,
            ).exists()
        )


class PesquisaTests(Fase3Base):
    def test_pesquisa_encontra_por_protocolo_nome_email_e_numero(self):
        pedido = self.criar_pedido()
        self.estudante.first_name = "Maria"
        self.estudante.last_name = "Silva"
        self.estudante.save(update_fields=["first_name", "last_name"])

        self.client.force_login(self.secretaria)
        url = reverse("pedidos:pesquisa")

        for termo in (
            pedido.protocolo,
            "Maria",
            self.estudante.email,
            self.estudante.perfil.numero_estudante,
        ):
            with self.subTest(termo=termo):
                resposta = self.client.get(url, {"q": termo})
                self.assertEqual(resposta.status_code, 200)
                self.assertIn(
                    pedido,
                    list(resposta.context["page_obj"]),
                )

    def test_pesquisa_e_proibida_a_credito_e_registo(self):
        url = reverse("pedidos:pesquisa")

        for utilizador in (self.credito, self.registo):
            with self.subTest(utilizador=utilizador.username):
                self.client.force_login(utilizador)
                self.assertEqual(
                    self.client.get(url).status_code,
                    403,
                )

        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_pesquisa_pagina_25_por_pagina(self):
        for _ in range(30):
            self.criar_pedido()

        self.client.force_login(self.secretaria)
        resposta = self.client.get(
            reverse("pedidos:pesquisa"),
            {"q": self.estudante.email},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["page_obj"].paginator.per_page, 25)
        self.assertEqual(len(resposta.context["page_obj"].object_list), 25)


class EntregaEFilaTests(Fase3Base):
    def test_marcar_entregue_so_funciona_com_estado_pronto(self):
        pedido = self.criar_pedido(
            etapa=Pedido.ETAPA_SECRETARIA_FINAL,
            estado=Pedido.ESTADO_EM_TRATAMENTO,
        )
        with self.assertRaises(ValidationError):
            services.marcar_entregue(pedido, self.secretaria)

        pedido = self.criar_pedido(
            etapa=Pedido.ETAPA_SECRETARIA_FINAL,
            estado=Pedido.ESTADO_PRONTO,
        )
        pedido = services.marcar_entregue(pedido, self.secretaria)

        self.assertEqual(pedido.estado, Pedido.ESTADO_ENTREGUE)
        self.assertEqual(pedido.entregue_por, self.secretaria)
        self.assertIsNotNone(pedido.entregue_em)
        self.assertEqual(
            pedido.decisoes.get().resultado,
            Decisao.RESULTADO_ENTREGUE,
        )

    def test_fila_da_secretaria_tem_tres_separadores_e_ordem_antiga(self):
        self.client.force_login(self.secretaria)
        url = reverse("pedidos:fila")

        casos = (
            (
                "novos",
                Pedido.ESTADO_EM_TRATAMENTO,
                Pedido.ETAPA_SECRETARIA_RECEPCAO,
            ),
            (
                "assinatura",
                Pedido.ESTADO_EM_TRATAMENTO,
                Pedido.ETAPA_SECRETARIA_FINAL,
            ),
            ("prontos", Pedido.ESTADO_PRONTO, None),
        )

        for tab, estado, etapa in casos:
            with self.subTest(tab=tab):
                resposta = self.client.get(url, {"tab": tab})
                self.assertEqual(resposta.status_code, 200)
                pedidos = list(resposta.context["pedidos"])
                for pedido in pedidos:
                    self.assertEqual(pedido.estado, estado)
                    if etapa is not None:
                        self.assertEqual(pedido.etapa_actual, etapa)
                self.assertEqual(
                    pedidos,
                    sorted(pedidos, key=lambda pedido: pedido.criado_em),
                )

    def test_fila_do_credito_registo_e_admin(self):
        url = reverse("pedidos:fila")

        self.client.force_login(self.credito)
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertTrue(resposta.context["pedidos"])
        for pedido in resposta.context["pedidos"]:
            self.assertEqual(pedido.estado, Pedido.ESTADO_EM_TRATAMENTO)
            self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_CREDITO)

        self.client.force_login(self.registo)
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        for pedido in resposta.context["pedidos"]:
            self.assertEqual(pedido.estado, Pedido.ESTADO_EM_TRATAMENTO)
            self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_REGISTO)

        self.client.force_login(self.admin)
        resposta = self.client.get(
            url,
            {"etapa": Pedido.ETAPA_REGISTO},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'name="etapa"')
        for pedido in resposta.context["pedidos"]:
            self.assertEqual(pedido.etapa_actual, Pedido.ETAPA_REGISTO)

    def test_inicio_mostra_contagens_da_fila_por_papel(self):
        self.client.force_login(self.secretaria)
        resposta = self.client.get(reverse("home"))
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("contagens_fila", resposta.context)
        self.assertContains(
            resposta,
            str(resposta.context["contagens_fila"]["novos"]),
        )


class VistaEstudanteTests(Fase3Base):
    def test_estudante_ve_etapa_simples_e_nao_ve_historico_interno(self):
        self.client.force_login(self.estudante)

        pedido = self.criar_pedido()
        pedido = services.aprovar(
            pedido,
            self.secretaria,
            "JUSTIFICACAO_INTERNA_SECRETA",
        )
        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[pedido.pk])
        )
        self.assertContains(resposta, "No controlo de crédito")
        self.assertNotContains(resposta, "JUSTIFICACAO_INTERNA_SECRETA")
        self.assertNotContains(resposta, "Histórico de decisões")

        resposta = self.client.get(reverse("pedidos:meus_pedidos"))
        self.assertContains(resposta, "No controlo de crédito")

    def test_estudante_ve_pronto_entregue_e_indeferido_com_motivo(self):
        self.client.force_login(self.estudante)

        pronto = self.criar_pedido(
            etapa=Pedido.ETAPA_SECRETARIA_FINAL
        )
        pronto = services.marcar_pronto(pronto, self.secretaria)
        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[pronto.pk])
        )
        self.assertContains(resposta, "Pronto para levantamento")

        entregue = self.criar_pedido(
            etapa=Pedido.ETAPA_SECRETARIA_FINAL,
            estado=Pedido.ESTADO_PRONTO,
        )
        entregue = services.marcar_entregue(entregue, self.secretaria)
        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[entregue.pk])
        )
        self.assertContains(resposta, "Entregue")

        motivo = "O comprovativo apresentado está ilegível."
        indeferido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        indeferido = services.indeferir(
            indeferido,
            self.credito,
            motivo,
        )
        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[indeferido.pk])
        )
        self.assertContains(resposta, "Indeferido")
        self.assertContains(resposta, motivo)


class AccoesMetodoTests(Fase3Base):
    def test_accoes_por_get_sao_rejeitadas_com_405(self):
        pedido = self.criar_pedido(etapa=Pedido.ETAPA_CREDITO)
        self.client.force_login(self.admin)

        for nome in (
            "aprovar",
            "indeferir",
            "marcar_pronto",
            "marcar_entregue",
            "carregar_extracto",
        ):
            with self.subTest(accao=nome):
                resposta = self.client.get(
                    reverse(f"pedidos:{nome}", args=[pedido.pk])
                )
                self.assertEqual(resposta.status_code, 405)
