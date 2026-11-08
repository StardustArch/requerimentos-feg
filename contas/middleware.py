from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

from .models import Perfil


class CompletarPerfilMiddleware:
    """Obriga os estudantes a preencher o grau e o curso.

    Staff, administradores e superutilizadores não são afectados. As páginas
    de login, logout e o próprio formulário de conclusão ficam sempre
    acessíveis, tal como os ficheiros estáticos.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._deve_redirecionar(request):
            return redirect("contas:completar_perfil")
        return self.get_response(request)

    def _deve_redirecionar(self, request):
        utilizador = request.user
        if not utilizador.is_authenticated:
            return False

        if utilizador.is_staff or utilizador.is_superuser:
            return False

        caminhos_excluidos = {
            reverse("contas:login"),
            reverse("contas:logout"),
            reverse("contas:completar_perfil"),
        }
        if request.path in caminhos_excluidos:
            return False

        static_url = str(settings.STATIC_URL)
        if static_url and request.path.startswith(static_url):
            return False

        perfil = getattr(utilizador, "perfil", None)
        if perfil is None or perfil.papel != Perfil.PAPEL_ESTUDANTE:
            return False

        return not perfil.perfil_completo
