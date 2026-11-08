from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from pedidos.models import Pedido

from .forms import CompletarPerfilForm
from .models import Perfil


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

    if request.method == "POST":
        form = CompletarPerfilForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil académico actualizado.")
            return redirect("home")
    else:
        form = CompletarPerfilForm(instance=perfil)

    return render(
        request,
        "contas/completar_perfil.html",
        {"form": form, "perfil": perfil},
    )
