from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import Perfil


class LoginComLimiteTests(TestCase):
    def setUp(self):
        cache.clear()
        self.password = "uma-palavra-passe-forte-123"
        self.utilizador = User.objects.create_user(
            username="maria_limite",
            email="maria.limite@ucm.ac.mz",
            password=self.password,
        )
        Perfil.objects.filter(user=self.utilizador).update(
            papel=Perfil.PAPEL_SECRETARIA
        )
        self.url = reverse("contas:login")

    def _falhar(self, username="maria_limite", ip="10.0.0.1", password="errada"):
        return self.client.post(
            self.url,
            {"username": username, "password": password},
            REMOTE_ADDR=ip,
        )

    def _sucesso(self, ip="10.0.0.1"):
        return self.client.post(
            self.url,
            {"username": "maria_limite", "password": self.password},
            REMOTE_ADDR=ip,
        )

    def test_cinco_falhas_bloqueiam_novas_tentativas_sem_expor_password(self):
        palavra_errada = "segredo-que-nao-deve-ir-para-o-log"
        with self.assertLogs("contas.login", level="WARNING") as registos:
            for _ in range(5):
                resposta = self._falhar(password=palavra_errada)
                self.assertEqual(resposta.status_code, 200)
            resposta = self._sucesso()

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Demasiadas tentativas falhadas")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn(
            palavra_errada,
            "\n".join(registos.output),
        )

    def test_um_login_bem_sucedido_limpa_o_contador_do_username(self):
        for _ in range(4):
            self._falhar()
        self.assertEqual(self._sucesso().status_code, 302)
        self.client.logout()

        for _ in range(4):
            self._falhar()
        resposta = self._sucesso()

        self.assertEqual(resposta.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_bloqueio_por_ip_nao_afecta_outros_utilizadores(self):
        for indice in range(20):
            self._falhar(
                username=f"utilizador_inexistente_{indice}",
                ip="10.0.0.50",
            )

        resposta = self._sucesso(ip="10.0.0.50")
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, "Demasiadas tentativas falhadas")

        resposta = self._sucesso(ip="10.0.0.51")
        self.assertEqual(resposta.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)
