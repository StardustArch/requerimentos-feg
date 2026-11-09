import tempfile
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .adapters import ContasSocialAccountAdapter, dominio_email_permitido
from .models import Curso, Perfil, extrair_numero_estudante


class LoginSocialGoogleTests(TestCase):
    """Simula o fluxo social sem chamar a API do Google."""

    def setUp(self):
        self.factory = RequestFactory()
        self.adapter = ContasSocialAccountAdapter()

    def _pedido(self):
        pedido = self.factory.get("/accounts/google/login/callback/")
        pedido.session = {}
        pedido._messages = FallbackStorage(pedido)
        return pedido

    def _social_login(self, email, *, verificado=True, uid="google-uid", extra=None):
        return SocialLogin(
            user=User(username="utilizador_google", email=email),
            account=SocialAccount(
                provider="google",
                uid=uid,
                extra_data=extra or {},
            ),
            email_addresses=[
                EmailAddress(email=email, verified=verificado, primary=True)
            ],
        )

    def test_dominio_permitido_aceita_login_e_cria_perfil_estudante(self):
        sociallogin = self._social_login("aluno@estudante.ucm.ac.mz")
        pedido = self._pedido()

        self.adapter.pre_social_login(pedido, sociallogin)
        self.adapter.save_user(pedido, sociallogin)

        utilizador = User.objects.get(email="aluno@estudante.ucm.ac.mz")
        self.assertEqual(utilizador.perfil.papel, Perfil.PAPEL_ESTUDANTE)
        self.assertEqual(utilizador.perfil.get_papel_display(), "Estudante")
        self.assertEqual(
            SocialAccount.objects.get(provider="google", uid="google-uid").user,
            utilizador,
        )

    def test_dominio_nao_permitido_e_rejeitado(self):
        dominios_invalidos = (
            "gmail.com",
            "evil-ucm.ac.mz",
            "ucm.ac.mz.evil.com",
        )

        for indice, dominio in enumerate(dominios_invalidos):
            with self.subTest(dominio=dominio):
                email = f"aluno@{dominio}"
                sociallogin = self._social_login(
                    email,
                    uid=f"google-invalido-{indice}",
                )

                with self.assertRaises(ImmediateHttpResponse) as contexto:
                    self.adapter.pre_social_login(self._pedido(), sociallogin)

                resposta = contexto.exception.response
                self.assertEqual(resposta.status_code, 302)
                self.assertEqual(resposta["Location"], settings.LOGIN_URL)
                self.assertFalse(
                    User.objects.filter(email__iexact=email).exists()
                )
                self.assertFalse(
                    SocialAccount.objects.filter(
                        uid=f"google-invalido-{indice}"
                    ).exists()
                )

    def test_dominio_permitido_exige_comparacao_exacta(self):
        self.assertTrue(dominio_email_permitido("aluno@ucm.ac.mz"))
        self.assertTrue(dominio_email_permitido("aluno@estudante.ucm.ac.mz"))
        self.assertFalse(dominio_email_permitido("aluno@evil-ucm.ac.mz"))
        self.assertFalse(dominio_email_permitido("aluno@ucm.ac.mz.evil.com"))

    def test_email_verified_falso_e_rejeitado(self):
        sociallogin = self._social_login(
            "aluno@ucm.ac.mz",
            verificado=False,
            extra={"email_verified": False},
        )

        with self.assertRaises(ImmediateHttpResponse) as contexto:
            self.adapter.pre_social_login(self._pedido(), sociallogin)

        self.assertEqual(contexto.exception.response.status_code, 302)
        self.assertFalse(
            User.objects.filter(email__iexact="aluno@ucm.ac.mz").exists()
        )
        self.assertEqual(SocialAccount.objects.count(), 0)

    def test_conta_local_com_mesmo_email_e_ligada_sem_duplicar(self):
        local = User.objects.create_user(
            username="maria",
            email="maria@ucm.ac.mz",
            password="segredo123",
        )
        sociallogin = self._social_login(
            "maria@ucm.ac.mz",
            uid="google-maria",
        )

        self.adapter.pre_social_login(self._pedido(), sociallogin)

        self.assertEqual(
            User.objects.filter(email__iexact="maria@ucm.ac.mz").count(),
            1,
        )
        self.assertEqual(sociallogin.user, local)
        conta = SocialAccount.objects.get(provider="google", uid="google-maria")
        self.assertEqual(conta.user, local)
        self.assertEqual(local.perfil.papel, Perfil.PAPEL_ESTUDANTE)

    def test_login_social_atribui_numero_a_perfis_de_estudante_sem_numero(self):
        local = User.objects.create_user(
            username="sem_numero",
            email="sem.numero@ucm.ac.mz",
            password="segredo123",
        )
        # Mudar o email sem voltar a guardar o perfil deixa-o sem número.
        local.email = "701234567@ucm.ac.mz"
        local.save()
        self.assertFalse(local.perfil.numero_estudante)

        sociallogin = self._social_login(
            "701234567@ucm.ac.mz",
            uid="google-numero",
        )
        self.adapter.pre_social_login(self._pedido(), sociallogin)

        local.perfil.refresh_from_db()
        self.assertEqual(local.perfil.numero_estudante, "701234567")

    def test_login_social_com_numero_duplicado_nao_rebenta(self):
        dono = User.objects.create_user(
            username="dono_numero",
            email="701234567@estudante.ucm.ac.mz",
        )
        self.assertEqual(dono.perfil.numero_estudante, "701234567")

        local = User.objects.create_user(
            username="duplicado_social",
            email="outro@ucm.ac.mz",
        )
        local.email = "701234567@ucm.ac.mz"
        local.save()

        sociallogin = self._social_login(
            "701234567@ucm.ac.mz",
            uid="google-duplicado",
        )
        with self.assertLogs("contas.models", level="WARNING"):
            self.adapter.pre_social_login(self._pedido(), sociallogin)

        local.perfil.refresh_from_db()
        self.assertFalse(local.perfil.numero_estudante)


class NumeroEstudanteTests(TestCase):
    def _estudante(self, username, email):
        return User.objects.create_user(
            username=username,
            email=email,
            password="teste12345",
        )

    def test_numero_e_extraido_do_email_sem_depender_do_dominio(self):
        self.assertEqual(
            extrair_numero_estudante("701234567@example.com"),
            "701234567",
        )
        self.assertEqual(
            extrair_numero_estudante("2023123456@estudante.ucm.ac.mz"),
            "2023123456",
        )
        self.assertEqual(
            extrair_numero_estudante("701234567@gmail.com"),
            "701234567",
        )
        self.assertIsNone(extrair_numero_estudante("aluno@ucm.ac.mz"))
        self.assertIsNone(extrair_numero_estudante(""))
        self.assertIsNone(extrair_numero_estudante("123@ucm.ac.mz"))

        estudante = self._estudante(
            "aluno_numerico",
            "701234567@estudante.ucm.ac.mz",
        )
        self.assertEqual(estudante.perfil.numero_estudante, "701234567")

    def test_mudar_email_e_guardar_recalcula_o_numero(self):
        estudante = self._estudante(
            "aluno_recalculo",
            "2023000001@estudante.ucm.ac.mz",
        )
        self.assertEqual(estudante.perfil.numero_estudante, "2023000001")

        estudante.email = "900000002@estudante.ucm.ac.mz"
        estudante.save()
        perfil = estudante.perfil
        perfil.save()

        perfil.refresh_from_db()
        self.assertEqual(perfil.numero_estudante, "900000002")

    def test_numero_duplicado_nao_e_atribuido_e_bloqueia_o_estudante(self):
        dono = self._estudante(
            "dono_do_numero",
            "701234567@estudante.ucm.ac.mz",
        )
        self.assertEqual(dono.perfil.numero_estudante, "701234567")

        with self.assertLogs("contas.models", level="WARNING"):
            duplicado = self._estudante(
                "numero_duplicado",
                "701234567@outro.ucm.ac.mz",
            )

        self.assertFalse(duplicado.perfil.numero_estudante)

        self.client.force_login(duplicado)
        resposta = self.client.get(reverse("home"))
        self.assertRedirects(
            resposta,
            reverse("contas:completar_perfil"),
            fetch_redirect_response=False,
        )
        resposta = self.client.get(reverse("contas:completar_perfil"))
        self.assertContains(resposta, "Contacta a Secretaria")

    def test_email_sem_numero_mostra_bloqueio_e_impede_pedido(self):
        estudante = self._estudante(
            "aluno_bloqueado",
            "aluno.sem.numero@estudante.ucm.ac.mz",
        )
        self.assertFalse(estudante.perfil.numero_estudante)
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("contas:completar_perfil"))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Contacta a Secretaria")
        self.assertContains(
            resposta,
            "aluno.sem.numero@estudante.ucm.ac.mz",
        )
        self.assertNotContains(resposta, 'name="curso"')
        self.assertNotContains(resposta, "id_numero_estudante")

        resposta = self.client.post(
            reverse("pedidos:novo_pedido"),
            {
                "tipo": "",
                "motivo": "Não deve ser criado.",
                "anexo_bi": SimpleUploadedFile("bi.pdf", b"%PDF-1.4\n"),
                "anexo_comprovativo": SimpleUploadedFile(
                    "comprovativo.pdf", b"%PDF-1.4\n"
                ),
            },
        )
        self.assertRedirects(
            resposta,
            reverse("contas:completar_perfil"),
            fetch_redirect_response=False,
        )
        self.assertFalse(estudante.pedidos.exists())

    def test_staff_com_email_nao_numerico_nao_e_bloqueado(self):
        secretaria = User.objects.create_user(
            username="secretaria_sem_numero",
            email="secretaria.teste@ucm.ac.mz",
            password="teste12345",
        )
        Perfil.objects.filter(user=secretaria).update(
            papel=Perfil.PAPEL_SECRETARIA
        )

        self.client.force_login(secretaria)
        resposta = self.client.get(reverse("home"))
        self.assertEqual(resposta.status_code, 200)

    def test_numero_nao_e_editavel_no_admin_nem_por_post(self):
        estudante = self._estudante(
            "aluno_nao_editavel",
            "2023000777@estudante.ucm.ac.mz",
        )
        curso = Curso.objects.create(
            nome="Gestão de Empresas",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        self.client.force_login(estudante)

        resposta = self.client.post(
            reverse("contas:completar_perfil"),
            {
                "curso": curso.pk,
                "numero_estudante": "999999999",
                "telefone": "84 000 0000",
            },
        )
        self.assertRedirects(resposta, reverse("home"))

        estudante.perfil.refresh_from_db()
        self.assertEqual(estudante.perfil.numero_estudante, "2023000777")
        self.assertEqual(estudante.perfil.curso, curso)
        self.assertEqual(estudante.perfil.grau, Perfil.GRAU_LICENCIATURA)

        # No admin o campo está desactivado e um POST forjado é ignorado.
        superutilizador = User.objects.create_superuser(
            username="admin_perfil",
            email="admin.perfil@ucm.ac.mz",
            password="teste12345",
        )
        pedido = RequestFactory().get("/admin/")
        pedido.user = superutilizador
        admin_perfil = admin.site._registry[Perfil]
        # Sendo um campo de leitura, o número nem sequer aparece no formulário
        # editável do admin.
        self.assertIn("numero_estudante", admin_perfil.readonly_fields)
        form_class = admin_perfil.get_form(pedido, obj=estudante.perfil)
        self.assertNotIn("numero_estudante", form_class.base_fields)

        self.client.force_login(superutilizador)
        resposta = self.client.post(
            reverse("admin:contas_perfil_change", args=[estudante.perfil.pk]),
            {
                "user": estudante.pk,
                "papel": Perfil.PAPEL_ESTUDANTE,
                "numero_estudante": "999999999",
                "curso": curso.pk,
                "grau": Perfil.GRAU_LICENCIATURA,
                "telefone": "84 111 1111",
            },
        )
        self.assertEqual(resposta.status_code, 302)
        estudante.perfil.refresh_from_db()
        self.assertEqual(estudante.perfil.numero_estudante, "2023000777")

    @override_settings(
        ATENDIMENTO_PRESENCIAL_INFO="Atendimento configurado para o teste."
    )
    def test_texto_de_apoio_presencial_aparece_nas_duas_paginas(self):
        texto = "Atendimento configurado para o teste."
        estudante = self._estudante(
            "aluno_texto_curso",
            "2023001111@estudante.ucm.ac.mz",
        )
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("contas:completar_perfil"))
        self.assertContains(resposta, "Não encontras o teu curso na lista?")
        self.assertContains(resposta, texto)
        self.assertIn("atendimento_presencial_info", resposta.context)
        self.assertIn("curso_nao_encontrado_texto", resposta.context)

        opcoes = resposta.context["form"].fields["curso"].choices
        self.assertFalse(
            any("outro" in str(etiqueta).lower() for _, etiqueta in opcoes)
        )

        bloqueado = self._estudante(
            "aluno_texto_bloqueio",
            "aluno.sem.numero@estudante.ucm.ac.mz",
        )
        self.client.force_login(bloqueado)

        resposta = self.client.get(reverse("contas:completar_perfil"))
        self.assertContains(resposta, texto)
        self.assertIn("atendimento_presencial_info", resposta.context)

    def test_curso_e_select_agrupado_e_fixa_o_grau(self):
        licenciatura = Curso.objects.create(
            nome="Economia",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        mestrado = Curso.objects.create(
            nome="Gestão de Empresas",
            grau=Perfil.GRAU_MESTRADO,
        )
        estudante = self._estudante(
            "aluno_curso",
            "2023000888@estudante.ucm.ac.mz",
        )
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("contas:completar_perfil"))
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "<optgroup")
        self.assertContains(resposta, licenciatura.nome)
        self.assertContains(resposta, mestrado.nome)
        self.assertContains(resposta, "readonly")
        self.assertContains(resposta, "Obtido do teu email institucional")

        resposta = self.client.post(
            reverse("contas:completar_perfil"),
            {"curso": mestrado.pk, "telefone": ""},
        )
        self.assertRedirects(resposta, reverse("home"))

        estudante.perfil.refresh_from_db()
        self.assertEqual(estudante.perfil.curso, mestrado)
        self.assertEqual(estudante.perfil.grau, Perfil.GRAU_MESTRADO)
        self.assertTrue(estudante.perfil.perfil_completo)


class CompletarPerfilMiddlewareTests(TestCase):
    def _utilizador(self, username, papel=Perfil.PAPEL_ESTUDANTE, email=""):
        utilizador = User.objects.create_user(
            username=username,
            email=email,
            password="teste12345",
        )
        Perfil.objects.filter(user=utilizador).update(papel=papel)
        return utilizador

    def test_estudante_sem_curso_e_sem_numero_e_redireccionado(self):
        estudante = self._utilizador("estudante_incompleto")
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("home"))

        self.assertRedirects(
            resposta,
            reverse("contas:completar_perfil"),
            fetch_redirect_response=False,
        )

    def test_estudante_com_curso_e_numero_entra_no_inicio(self):
        estudante = self._utilizador(
            "estudante_completo",
            email="2023000456@estudante.ucm.ac.mz",
        )
        perfil = estudante.perfil
        curso = Curso.objects.create(
            nome="Informática de Gestão",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        perfil.curso = curso
        perfil.grau = curso.grau
        perfil.save(update_fields=["curso", "grau"])
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("home"))

        self.assertEqual(resposta.status_code, 200)

    def test_estudante_com_curso_mas_sem_numero_fica_bloqueado(self):
        estudante = self._utilizador(
            "estudante_sem_numero",
            email="aluno.sem.numero@estudante.ucm.ac.mz",
        )
        perfil = estudante.perfil
        curso = Curso.objects.create(
            nome="Gestão",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        perfil.curso = curso
        perfil.grau = curso.grau
        perfil.save(update_fields=["curso", "grau"])
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("home"))
        self.assertRedirects(
            resposta,
            reverse("contas:completar_perfil"),
            fetch_redirect_response=False,
        )

        resposta = self.client.get(reverse("contas:completar_perfil"))
        self.assertContains(resposta, "Contacta a Secretaria")

    def test_staff_e_superutilizador_nao_sao_obrigados(self):
        secretaria = self._utilizador(
            "secretaria_sem_dados",
            Perfil.PAPEL_SECRETARIA,
        )
        superutilizador = User.objects.create_superuser(
            username="root_sem_dados",
            email="root@ucm.ac.mz",
            password="teste12345",
        )

        for utilizador in (secretaria, superutilizador):
            with self.subTest(utilizador=utilizador.username):
                self.client.force_login(utilizador)
                resposta = self.client.get(reverse("home"))
                self.assertEqual(resposta.status_code, 200)

    def test_completar_perfil_guarda_e_liberta_o_acesso(self):
        estudante = self._utilizador(
            "estudante_formulario",
            email="2023000999@estudante.ucm.ac.mz",
        )
        curso = Curso.objects.create(
            nome="Gestão de Empresas",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        self.client.force_login(estudante)

        resposta = self.client.post(
            reverse("contas:completar_perfil"),
            {
                "curso": curso.pk,
                "numero_estudante": "999999999",
                "telefone": "",
            },
        )

        self.assertRedirects(resposta, reverse("home"))
        estudante.perfil.refresh_from_db()
        self.assertEqual(estudante.perfil.curso, curso)
        self.assertEqual(estudante.perfil.grau, Perfil.GRAU_LICENCIATURA)
        self.assertEqual(estudante.perfil.numero_estudante, "2023000999")

        resposta = self.client.get(reverse("home"))
        self.assertEqual(resposta.status_code, 200)


@override_settings(ROOT_URLCONF="contas.test_urls")
class DecoradoresPermissoesTests(TestCase):
    URLS = (
        "probe_estudante",
        "probe_secretaria",
        "probe_credito",
        "probe_registo",
        "probe_staff",
        "probe_admin",
    )

    def setUp(self):
        self._contador = 0

    def _utilizador(self, username, papel, superuser=False):
        self._contador += 1
        email = (
            f"{710000000 + self._contador}@estudante.ucm.ac.mz"
            if papel == Perfil.PAPEL_ESTUDANTE
            else f"{username}@ucm.ac.mz"
        )

        if superuser:
            utilizador = User.objects.create_superuser(
                username=username,
                email=email,
                password="teste12345",
            )
        else:
            utilizador = User.objects.create_user(
                username=username,
                email=email,
                password="teste12345",
            )

        curso = None
        if papel == Perfil.PAPEL_ESTUDANTE:
            curso = Curso.objects.create(
                nome=f"Curso {self._contador}",
                grau=Perfil.GRAU_LICENCIATURA,
            )

        Perfil.objects.filter(user=utilizador).update(
            papel=papel,
            grau=(
                Perfil.GRAU_LICENCIATURA
                if papel == Perfil.PAPEL_ESTUDANTE
                else None
            ),
            curso=curso,
        )
        return utilizador

    def test_cada_decorador_devolve_403_ao_papel_errado(self):
        casos = (
            ("probe_estudante", Perfil.PAPEL_SECRETARIA),
            ("probe_secretaria", Perfil.PAPEL_ESTUDANTE),
            ("probe_credito", Perfil.PAPEL_ESTUDANTE),
            ("probe_registo", Perfil.PAPEL_ESTUDANTE),
            ("probe_staff", Perfil.PAPEL_ESTUDANTE),
            ("probe_admin", Perfil.PAPEL_SECRETARIA),
        )

        for indice, (nome_url, papel_errado) in enumerate(casos):
            with self.subTest(nome_url=nome_url, papel=papel_errado):
                utilizador = self._utilizador(
                    f"utilizador_errado_{indice}",
                    papel_errado,
                )
                self.client.force_login(utilizador)
                resposta = self.client.get(reverse(nome_url))
                self.assertEqual(resposta.status_code, 403)

    def test_admin_passa_em_todos_os_decoradores(self):
        administrador = self._utilizador(
            "administrador_probe",
            Perfil.PAPEL_ADMIN,
        )
        self.client.force_login(administrador)

        for nome_url in self.URLS:
            with self.subTest(nome_url=nome_url):
                resposta = self.client.get(reverse(nome_url))
                self.assertEqual(resposta.status_code, 200)

    def test_superutilizador_passa_nos_decoradores_de_staff(self):
        superutilizador = self._utilizador(
            "superutilizador_probe",
            Perfil.PAPEL_ESTUDANTE,
            superuser=True,
        )
        self.client.force_login(superutilizador)

        for nome_url in (
            "probe_secretaria",
            "probe_credito",
            "probe_registo",
            "probe_staff",
            "probe_admin",
        ):
            with self.subTest(nome_url=nome_url):
                resposta = self.client.get(reverse(nome_url))
                self.assertEqual(resposta.status_code, 200)


class ImportarUtilizadoresTests(TestCase):
    def _csv(self, conteudo):
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        caminho = Path(pasta.name) / "utilizadores.csv"
        caminho.write_text(conteudo, encoding="utf-8")
        return caminho

    def test_importar_utilizadores_e_idempotente(self):
        caminho = self._csv(
            "nome,email,papel,curso,grau\n"
            "Maria Silva,maria@ucm.ac.mz,secretaria,,\n"
            "João Costa,2023001@estudante.ucm.ac.mz,estudante,"
            "Informática,licenciatura\n"
        )

        call_command("importar_utilizadores", str(caminho), stdout=StringIO())
        maria = User.objects.get(email="maria@ucm.ac.mz")
        password_inicial = maria.password
        contagens_iniciais = (
            User.objects.count(),
            Perfil.objects.count(),
            SocialAccount.objects.count(),
        )

        call_command("importar_utilizadores", str(caminho), stdout=StringIO())

        self.assertEqual(
            (
                User.objects.count(),
                Perfil.objects.count(),
                SocialAccount.objects.count(),
            ),
            contagens_iniciais,
        )
        maria.refresh_from_db()
        self.assertEqual(maria.password, password_inicial)
        self.assertEqual(maria.perfil.papel, Perfil.PAPEL_SECRETARIA)
        self.assertFalse(maria.perfil.numero_estudante)

        joao = User.objects.get(email="2023001@estudante.ucm.ac.mz")
        self.assertEqual(joao.perfil.papel, Perfil.PAPEL_ESTUDANTE)
        self.assertEqual(joao.perfil.numero_estudante, "2023001")
        self.assertEqual(joao.perfil.curso.nome, "Informática")
        self.assertEqual(joao.perfil.grau, Perfil.GRAU_LICENCIATURA)

    def test_importar_ignora_estudante_sem_numero_e_aceita_staff(self):
        caminho = self._csv(
            "nome,email,papel,curso,grau\n"
            "Ana Silva,ana@ucm.ac.mz,admin,,,\n"
            "Rui Santos,rui.santos@ucm.ac.mz,secretaria,,,\n"
            "Sem Numero,aluno.sem.numero@estudante.ucm.ac.mz,"
            "estudante,Gestão,licenciatura\n"
        )
        erros = StringIO()

        call_command(
            "importar_utilizadores",
            str(caminho),
            stdout=StringIO(),
            stderr=erros,
        )

        self.assertTrue(User.objects.filter(email="ana@ucm.ac.mz").exists())
        self.assertTrue(User.objects.filter(email="rui.santos@ucm.ac.mz").exists())
        self.assertFalse(
            User.objects.filter(
                email="aluno.sem.numero@estudante.ucm.ac.mz"
            ).exists()
        )
        self.assertIn(
            "aluno.sem.numero@estudante.ucm.ac.mz",
            erros.getvalue(),
        )

    def test_importar_utilizadores_com_sem_password(self):
        caminho = self._csv(
            "nome,email,papel,curso,grau\n"
            "Ana Silva,ana@ucm.ac.mz,admin,,\n"
        )

        call_command(
            "importar_utilizadores",
            str(caminho),
            "--sem-password",
            stdout=StringIO(),
        )

        ana = User.objects.get(email="ana@ucm.ac.mz")
        self.assertFalse(ana.has_usable_password())
        self.assertEqual(ana.perfil.papel, Perfil.PAPEL_ADMIN)


class CarregarCursosTests(TestCase):
    def test_carregar_cursos_e_idempotente_e_cria_18_cursos(self):
        saida = StringIO()
        call_command("carregar_cursos", stdout=saida)

        self.assertIn("18 criado(s)", saida.getvalue())
        self.assertEqual(Curso.objects.count(), 18)
        self.assertEqual(
            Curso.objects.filter(grau=Perfil.GRAU_LICENCIATURA).count(),
            8,
        )
        self.assertEqual(
            Curso.objects.filter(grau=Perfil.GRAU_MESTRADO).count(),
            9,
        )
        self.assertEqual(
            Curso.objects.filter(grau=Perfil.GRAU_DOUTORAMENTO).count(),
            1,
        )

        contabilidade = Curso.objects.filter(
            nome="Contabilidade e Auditoria"
        )
        self.assertEqual(contabilidade.count(), 2)
        self.assertSetEqual(
            set(contabilidade.values_list("grau", flat=True)),
            {Perfil.GRAU_LICENCIATURA, Perfil.GRAU_MESTRADO},
        )

        saida = StringIO()
        call_command("carregar_cursos", stdout=saida)

        self.assertIn("0 criado(s)", saida.getvalue())
        self.assertEqual(Curso.objects.count(), 18)
        self.assertEqual(
            Curso.objects.filter(nome="Contabilidade e Auditoria").count(),
            2,
        )


class LoginPageGoogleTests(TestCase):
    def test_botao_google_aparece_e_preserva_o_next(self):
        next_url = reverse("home")

        with override_settings(
            GOOGLE_CLIENT_ID="cliente-teste",
            GOOGLE_CLIENT_SECRET="segredo-teste",
        ):
            resposta = self.client.get(
                reverse("contas:login"),
                {"next": next_url},
            )

        self.assertContains(resposta, "Entrar com Google institucional")
        self.assertContains(
            resposta,
            "Acesso de pessoal e contas de demonstração",
        )
        self.assertContains(resposta, urlencode({"next": next_url}))

    def test_botao_google_fica_escondido_sem_credenciais(self):
        with override_settings(
            GOOGLE_CLIENT_ID="",
            GOOGLE_CLIENT_SECRET="",
        ):
            resposta = self.client.get(reverse("contas:login"))

        self.assertNotContains(resposta, "Entrar com Google")
        self.assertContains(
            resposta,
            "Acesso de pessoal e contas de demonstração",
        )
