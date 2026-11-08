from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from pedidos.models import Pedido

from .forms import CompletarPerfilForm
from .models import Curso, Perfil


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
