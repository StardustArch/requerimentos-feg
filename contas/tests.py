import tempfile
from io import StringIO
from pathlib import Path
from urllib.parse import urlencode

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from .adapters import ContasSocialAccountAdapter, dominio_email_permitido
from .models import Perfil


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


class CompletarPerfilMiddlewareTests(TestCase):
    def _utilizador(self, username, papel=Perfil.PAPEL_ESTUDANTE):
        utilizador = User.objects.create_user(
            username=username,
            password="teste12345",
        )
        Perfil.objects.filter(user=utilizador).update(papel=papel)
        return utilizador

    def test_estudante_sem_grau_e_curso_e_redireccionado(self):
        estudante = self._utilizador("estudante_incompleto")
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("home"))

        self.assertRedirects(
            resposta,
            reverse("contas:completar_perfil"),
            fetch_redirect_response=False,
        )

    def test_estudante_com_grau_e_curso_entra_no_inicio(self):
        estudante = self._utilizador("estudante_completo")
        perfil = estudante.perfil
        perfil.grau = Perfil.GRAU_LICENCIATURA
        perfil.curso = "Informática de Gestão"
        perfil.save(update_fields=["grau", "curso"])
        self.client.force_login(estudante)

        resposta = self.client.get(reverse("home"))

        self.assertEqual(resposta.status_code, 200)

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
        estudante = self._utilizador("estudante_formulario")
        self.client.force_login(estudante)

        resposta = self.client.post(
            reverse("contas:completar_perfil"),
            {
                "grau": Perfil.GRAU_LICENCIATURA,
                "curso": "Gestão de Empresas",
                "numero_estudante": "2023123456",
                "telefone": "",
            },
        )

        self.assertRedirects(resposta, reverse("home"))
        estudante.perfil.refresh_from_db()
        self.assertEqual(estudante.perfil.grau, Perfil.GRAU_LICENCIATURA)
        self.assertEqual(estudante.perfil.curso, "Gestão de Empresas")
        self.assertEqual(estudante.perfil.numero_estudante, "2023123456")

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

    def _utilizador(self, username, papel, superuser=False):
        if superuser:
            utilizador = User.objects.create_superuser(
                username=username,
                email=f"{username}@ucm.ac.mz",
                password="teste12345",
            )
        else:
            utilizador = User.objects.create_user(
                username=username,
                password="teste12345",
            )

        Perfil.objects.filter(user=utilizador).update(
            papel=papel,
            grau=(
                Perfil.GRAU_LICENCIATURA
                if papel == Perfil.PAPEL_ESTUDANTE
                else None
            ),
            curso=(
                "Informática de Gestão"
                if papel == Perfil.PAPEL_ESTUDANTE
                else None
            ),
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
            "nome,email,papel,numero_estudante,curso,grau\n"
            "Maria Silva,maria@ucm.ac.mz,secretaria,,,\n"
            "João Costa,joao@estudante.ucm.ac.mz,estudante,"
            "2023001,Informática,licenciatura\n"
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

        joao = User.objects.get(email="joao@estudante.ucm.ac.mz")
        self.assertEqual(joao.perfil.papel, Perfil.PAPEL_ESTUDANTE)
        self.assertEqual(joao.perfil.numero_estudante, "2023001")
        self.assertEqual(joao.perfil.curso, "Informática")
        self.assertEqual(joao.perfil.grau, Perfil.GRAU_LICENCIATURA)

    def test_importar_utilizadores_com_sem_password(self):
        caminho = self._csv(
            "nome,email,papel,numero_estudante,curso,grau\n"
            "Ana Silva,ana@ucm.ac.mz,admin,,,\n"
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
        self.assertContains(resposta, "bi-google")
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
