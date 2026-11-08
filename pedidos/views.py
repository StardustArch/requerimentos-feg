import os
from mimetypes import guess_type

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from contas.models import Perfil
from contas.permissoes import e_admin, estudante_required, papel_utilizador

from .forms import NovoPedidoForm
from .models import Anexo, Pedido, TipoDocumento

TIPOS_DE_ANEXO = (
    (Anexo.TIPO_BI, "anexo_bi"),
    (Anexo.TIPO_COMPROVATIVO, "anexo_comprovativo"),
)

ALIASES_ANEXOS = {
    "bi": "anexo_bi",
    "ficheiro_bi": "anexo_bi",
    "comprovativo": "anexo_comprovativo",
    "ficheiro_comprovativo": "anexo_comprovativo",
}


def _tipo_activo(valor):
    try:
        pk = int(valor)
    except (TypeError, ValueError):
        return None
    return TipoDocumento.objects.filter(pk=pk, activo=True).first()


def _contexto_resumo(utilizador, tipo):
    perfil = getattr(utilizador, "perfil", None)
    contexto = {"tipo": tipo, "perfil": perfil}

    if tipo is not None and perfil is not None and perfil.grau:
        contexto.update(
            {
                "total": tipo.total_com_formulario(perfil.grau),
                "prazo_estimado_dias": tipo.prazo_estimado_dias,
                "grau": perfil.grau,
                "grau_display": perfil.get_grau_display(),
            }
        )
    return contexto


def _dados_do_formulario(request):
    """Permite nomes alternativos para os campos dos dois anexos."""

    dados = request.POST.copy()
    ficheiros = request.FILES.copy()

    for origem in list(ficheiros.keys()):
        destino = ALIASES_ANEXOS.get(origem)
        if destino and destino not in ficheiros:
            ficheiros[destino] = ficheiros[origem]

    return dados, ficheiros


@login_required
@estudante_required
def novo_pedido(request):
    perfil = request.user.perfil

    if request.method == "POST":
        dados, ficheiros = _dados_do_formulario(request)
        form = NovoPedidoForm(dados, ficheiros)

        if form.is_valid():
            anexos_guardados = []
            try:
                with transaction.atomic():
                    pedido = form.save(commit=False)
                    pedido.estudante = request.user
                    pedido.grau = perfil.grau
                    pedido.save()

                    for tipo_anexo, campo in TIPOS_DE_ANEXO:
                        ficheiro = form.cleaned_data[campo]
                        anexo = Anexo.objects.create(
                            pedido=pedido,
                            tipo=tipo_anexo,
                            ficheiro=ficheiro,
                            nome_original=ficheiro.name,
                            visivel_ao_estudante=True,
                            carregado_por=request.user,
                        )
                        anexos_guardados.append(anexo)
            except Exception:
                for anexo in anexos_guardados:
                    if anexo.ficheiro:
                        anexo.ficheiro.delete(save=False)
                raise

            messages.success(
                request,
                f"Pedido {pedido.protocolo} submetido com sucesso.",
            )
            return redirect("pedidos:pedido_detalhe", pk=pedido.pk)
    else:
        form = NovoPedidoForm()

    tipo = None
    if form.is_bound:
        tipo = _tipo_activo(form.data.get("tipo"))
    elif request.GET.get("tipo"):
        tipo = _tipo_activo(request.GET.get("tipo"))

    contexto = {
        "form": form,
        "perfil": perfil,
        **_contexto_resumo(request.user, tipo),
    }
    return render(request, "pedidos/novo_pedido.html", contexto)


@login_required
@estudante_required
def resumo_pedido(request):
    tipo = _tipo_activo(
        request.GET.get("tipo")
        or request.GET.get("id_tipo")
        or request.GET.get("tipo_id")
    )
    return render(
        request,
        "pedidos/_resumo_pedido.html",
        _contexto_resumo(request.user, tipo),
    )


@login_required
@estudante_required
def meus_pedidos(request):
    pedidos = (
        Pedido.objects.filter(estudante=request.user)
        .select_related("tipo")
        .order_by("-criado_em")
    )
    return render(request, "pedidos/meus_pedidos.html", {"pedidos": pedidos})


@login_required
@estudante_required
def pedido_detalhe(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("tipo"),
        pk=pk,
        estudante=request.user,
    )
    anexos = pedido.anexos.filter(visivel_ao_estudante=True)
    return render(
        request,
        "pedidos/pedido_detalhe.html",
        {"pedido": pedido, "anexos": anexos},
    )


def _pode_descarregar(utilizador, anexo):
    if not utilizador or not utilizador.is_authenticated:
        return False

    if e_admin(utilizador):
        return True

    papel = papel_utilizador(utilizador)
    if papel == Perfil.PAPEL_SECRETARIA:
        return True
    if papel == Perfil.PAPEL_CREDITO:
        return anexo.pedido.etapa_actual == Pedido.ETAPA_CREDITO
    if papel == Perfil.PAPEL_REGISTO:
        return anexo.pedido.etapa_actual == Pedido.ETAPA_REGISTO
    if papel == Perfil.PAPEL_ESTUDANTE:
        return (
            anexo.pedido.estudante_id == utilizador.pk
            and anexo.visivel_ao_estudante
        )
    return False


@login_required
def anexo_download(request, pk):
    anexo = get_object_or_404(
        Anexo.objects.select_related("pedido"),
        pk=pk,
    )

    if not _pode_descarregar(request.user, anexo):
        raise Http404("Anexo não encontrado.")

    if not anexo.ficheiro:
        raise Http404("Anexo não encontrado.")

    try:
        ficheiro = anexo.ficheiro.open("rb")
    except FileNotFoundError:
        raise Http404("Anexo não encontrado.") from None

    nome = anexo.nome_original or os.path.basename(anexo.ficheiro.name)
    content_type = guess_type(nome)[0] or "application/octet-stream"
    resposta = FileResponse(
        ficheiro,
        as_attachment=True,
        filename=nome,
        content_type=content_type,
    )
    resposta["X-Content-Type-Options"] = "nosniff"
    return resposta
