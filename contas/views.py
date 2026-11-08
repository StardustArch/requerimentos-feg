import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import redirect, render

from pedidos.models import Pedido

from .forms import CompletarPerfilForm
from .models import Curso, Perfil

logger = logging.getLogger("contas.login")

CHAVE_FALTAS_USERNAME = "login:faltas:username:{username}"
CHAVE_FALTAS_IP = "login:faltas:ip:{ip}"


def _ip_do_pedido(request):
    return (request.META.get("REMOTE_ADDR") or "").strip() or "desconhecido"


def _chave_username(username):
    return CHAVE_FALTAS_USERNAME.format(username=username.casefold())


def _chave_ip(ip):
    return CHAVE_FALTAS_IP.format(ip=ip)


def _incrementar_faltas(chave, janela_segundos):
    if cache.add(chave, 1, timeout=janela_segundos):
        return 1
    try:
        return cache.incr(chave)
    except ValueError:
        # A chave expirou entre o add e o incr.
        cache.add(chave, 1, timeout=janela_segundos)
        return cache.get(chave, 1)


def _limites_login():
    return (
        getattr(settings, "LOGIN_MAX_TENTATIVAS_USERNAME", 5),
        getattr(settings, "LOGIN_MAX_TENTATIVAS_IP", 20),
        getattr(settings, "LOGIN_JANELA_MINUTOS", 15),
    )


def _login_bloqueado(username, ip):
    max_username, max_ip, _ = _limites_login()
    faltas_username = cache.get(_chave_username(username), 0) if username else 0
    faltas_ip = cache.get(_chave_ip(ip), 0)
    return faltas_username >= max_username or faltas_ip >= max_ip


class LoginViewComLimite(auth_views.LoginView):
    """Login clássico com limite de tentativas por utilizador e por IP."""

    template_name = "contas/login.html"

    def post(self, request, *args, **kwargs):
        username = (request.POST.get("username") or "").strip()
        ip = _ip_do_pedido(request)
        max_username, max_ip, janela_minutos = _limites_login()

        if _login_bloqueado(username, ip):
            logger.warning(
                "Tentativa de login bloqueada por excesso de falhas "
                "(username=%r ip=%s).",
                username,
                ip,
            )
            return self.render_to_response(
                self.get_context_data(
                    form=self.get_form(),
                    bloqueado=True,
                    mensagem_bloqueio=(
                        "Demasiadas tentativas falhadas. Por segurança, o "
                        "acesso está temporariamente bloqueado. Tente "
                        f"novamente dentro de {janela_minutos} minutos."
                    ),
                )
            )

        response = super().post(request, *args, **kwargs)

        if request.user.is_authenticated:
            # Um login bem sucedido limpa apenas o contador do utilizador.
            if username:
                cache.delete(_chave_username(username))
            return response

        janela_segundos = janela_minutos * 60
        faltas_username = (
            _incrementar_faltas(
                _chave_username(username),
                janela_segundos,
            )
            if username
            else 0
        )
        faltas_ip = _incrementar_faltas(
            _chave_ip(ip),
            janela_segundos,
        )

        if faltas_username >= max_username or faltas_ip >= max_ip:
            logger.warning(
                "Limite de tentativas de login atingido; novas tentativas "
                "ficam bloqueadas (username=%r faltas_username=%s ip=%s "
                "faltas_ip=%s).",
                username,
                faltas_username,
                ip,
                faltas_ip,
            )

        return response


def _contagens_fila():
    return {
        "novos": Pedido.objects.filter(
            estado=Pedido.ESTADO_EM_TRATAMENTO,
            etapa_actual=Pedido.ETAPA_SECRETARIA_RECEPCAO,
        ).count(),
        "credito": Pedido.objects.filter(
            estado=Pedido.ESTADO_EM_TRATAMENTO,
            etapa_actual=Pedido.ETAPA_CREDITO,
        ).count(),
        "registo": Pedido.objects.filter(
            estado=Pedido.ESTADO_EM_TRATAMENTO,
            etapa_actual=Pedido.ETAPA_REGISTO,
        ).count(),
        "assinatura": Pedido.objects.filter(
            estado=Pedido.ESTADO_EM_TRATAMENTO,
            etapa_actual=Pedido.ETAPA_SECRETARIA_FINAL,
        ).count(),
        "prontos": Pedido.objects.filter(
            estado=Pedido.ESTADO_PRONTO,
        ).count(),
    }


@login_required
def dashboard_redirect(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)
    return render(
        request,
        "contas/home.html",
        {
            "perfil": perfil,
            "contagens_fila": _contagens_fila(),
        },
    )


@login_required
def completar_perfil(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if perfil.papel != Perfil.PAPEL_ESTUDANTE:
        return redirect("home")

    # Sem número de estudante identificado a partir do email: página de
    # bloqueio, sem formulário. O estudante não pode submeter pedidos.
    if not perfil.numero_estudante:
        messages.error(
            request,
            "Não foi possível identificar o teu número de estudante a partir do "
            f"email {request.user.email or ''}. Contacta a Secretaria.",
        )
        return render(
            request, "contas/bloqueio_numero.html", {"perfil": perfil}
        )

    if request.method == "POST":
        dados = request.POST.copy()
        dados.pop("numero_estudante", None)  # nunca editável à mão
        form = CompletarPerfilForm(dados, instance=perfil)
        if form.is_valid():
            perfil = form.save(commit=False)
            # O curso escolhido fixa o grau.
            perfil.grau = perfil.curso.grau
            perfil.save()
            messages.success(request, "Perfil académico actualizado.")
            return redirect("home")
    else:
        form = CompletarPerfilForm(instance=perfil)

    cursos_por_grau = []
    for grau, grau_display in Perfil.GRAU_CHOICES:
        cursos = (
            Curso.objects.filter(grau=grau, activo=True).order_by("nome")
        )
        if cursos:
            cursos_por_grau.append(
                {
                    "grau": grau,
                    "grau_display": grau_display,
                    "cursos": cursos,
                }
            )

    return render(
        request,
        "contas/completar_perfil.html",
        {
            "form": form,
            "perfil": perfil,
            "cursos_por_grau": cursos_por_grau,
        },
    )
