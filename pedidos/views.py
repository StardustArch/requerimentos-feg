import os
from datetime import timedelta
from mimetypes import guess_type

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from contas.models import Perfil
from contas.permissoes import (
    e_admin,
    estudante_required,
    papel_utilizador,
    secretaria_required,
    staff_required,
)

from . import services
from .forms import NovoPedidoForm
from .models import Anexo, Decisao, Pedido, TipoDocumento
from .validators import validar_anexo

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

PERIODOS_PAINEL = (
    ("30d", "Últimos 30 dias"),
    ("mes", "Este mês"),
    ("ano", "Este ano"),
    ("tudo", "Tudo"),
)
PERIODO_PAINEL_PREDEFINIDO = "30d"


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
                "tipo": tipo,
                "taxa_base": tipo.taxa_base(perfil.grau),
                "iva": tipo.iva(perfil.grau),
                "total": tipo.total(perfil.grau),
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
        "max_anexo_mb": settings.MAX_ANEXO_MB,
        "formatos_aceites": "PDF, JPG/JPEG ou PNG",
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
    pagina = Paginator(pedidos, 25).get_page(request.GET.get("page"))
    return render(
        request,
        "pedidos/meus_pedidos.html",
        {"pedidos": pagina, "page_obj": pagina},
    )


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

    if anexo.tipo == Anexo.TIPO_EXTRACTO:
        return (
            papel == Perfil.PAPEL_CREDITO
            and anexo.pedido.etapa_actual == Pedido.ETAPA_CREDITO
        )

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


def _pedidos_na_etapa(etapa):
    return (
        Pedido.objects.filter(
            estado=Pedido.ESTADO_EM_TRATAMENTO,
            etapa_actual=etapa,
        )
        .select_related("estudante__perfil", "tipo")
        .order_by("criado_em")
    )


def _paginar(request, pedidos):
    """Pagina uma fila, tolerando listas vazias e páginas inválidas."""
    return Paginator(pedidos, 25).get_page(request.GET.get("page"))


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
@staff_required
def fila(request):
    papel = papel_utilizador(request.user)
    admin = e_admin(request.user)
    contagens = _contagens_fila()
    etapas = Pedido.ETAPA_CHOICES

    if admin:
        etapa = request.GET.get("etapa") or Pedido.ETAPA_SECRETARIA_RECEPCAO
        if etapa not in dict(etapas):
            etapa = Pedido.ETAPA_SECRETARIA_RECEPCAO
        pedidos = _pedidos_na_etapa(etapa)
        contexto = {
            "admin": True,
            "etapa": etapa,
            "etapas": etapas,
            "pedidos": pedidos,
            "contagens": contagens,
        }
    elif papel == Perfil.PAPEL_SECRETARIA:
        tab = request.GET.get("tab") or "novos"
        if tab == "assinatura":
            pedidos = _pedidos_na_etapa(Pedido.ETAPA_SECRETARIA_FINAL)
        elif tab == "prontos":
            pedidos = (
                Pedido.objects.filter(estado=Pedido.ESTADO_PRONTO)
                .select_related("estudante__perfil", "tipo")
                .order_by("criado_em")
            )
        else:
            tab = "novos"
            pedidos = _pedidos_na_etapa(Pedido.ETAPA_SECRETARIA_RECEPCAO)
        contexto = {
            "admin": False,
            "tab": tab,
            "pedidos": pedidos,
            "contagens": contagens,
        }
    elif papel == Perfil.PAPEL_CREDITO:
        contexto = {
            "admin": False,
            "etapa": Pedido.ETAPA_CREDITO,
            "pedidos": _pedidos_na_etapa(Pedido.ETAPA_CREDITO),
            "contagens": contagens,
        }
    elif papel == Perfil.PAPEL_REGISTO:
        contexto = {
            "admin": False,
            "etapa": Pedido.ETAPA_REGISTO,
            "pedidos": _pedidos_na_etapa(Pedido.ETAPA_REGISTO),
            "contagens": contagens,
        }
    else:
        raise PermissionDenied("Sem acesso à fila de trabalho.")

    pagina = _paginar(request, contexto["pedidos"])
    contexto["pedidos"] = pagina
    contexto["page_obj"] = pagina
    return render(request, "pedidos/fila.html", contexto)


@login_required
@secretaria_required
def pesquisa(request):
    pedidos = Pedido.objects.select_related(
        "estudante__perfil",
        "tipo",
    )

    q = (request.GET.get("q") or "").strip()
    if q:
        pedidos = pedidos.filter(
            Q(protocolo__icontains=q)
            | Q(estudante__first_name__icontains=q)
            | Q(estudante__last_name__icontains=q)
            | Q(estudante__username__icontains=q)
            | Q(estudante__email__icontains=q)
            | Q(estudante__perfil__numero_estudante__icontains=q)
        )

    estado = request.GET.get("estado") or ""
    if estado in dict(Pedido.ESTADO_CHOICES):
        pedidos = pedidos.filter(estado=estado)

    etapa = request.GET.get("etapa") or ""
    if etapa in dict(Pedido.ETAPA_CHOICES):
        pedidos = pedidos.filter(etapa_actual=etapa)

    tipo_id = request.GET.get("tipo") or ""
    if tipo_id:
        try:
            pedidos = pedidos.filter(tipo_id=int(tipo_id))
        except (TypeError, ValueError):
            pedidos = pedidos.none()

    pedidos = pedidos.order_by("-criado_em")
    paginador = Paginator(pedidos, 25)
    pagina = paginador.get_page(request.GET.get("page"))

    contexto = {
        "page_obj": pagina,
        "pedidos": pagina,
        "q": q,
        "estado": estado,
        "etapa": etapa,
        "tipo": tipo_id,
        "estados": Pedido.ESTADO_CHOICES,
        "etapas": Pedido.ETAPA_CHOICES,
        "tipos": TipoDocumento.objects.order_by("nome"),
    }
    return render(request, "pedidos/pesquisa.html", contexto)


def _inicio_periodo_painel(periodo):
    agora = timezone.now()
    if periodo == "30d":
        return agora - timedelta(days=30)
    if periodo == "mes":
        local = timezone.localtime(agora)
        return local.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    if periodo == "ano":
        local = timezone.localtime(agora)
        return local.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    return None


def _dados_grafico_estados(contagens, escolhas):
    return {
        "labels": [rotulo for _, rotulo in escolhas],
        "valores": [contagens.get(valor, 0) for valor, _ in escolhas],
    }


@login_required
@staff_required
def painel(request):
    """Indicadores agregados dos pedidos, sem dados pessoais dos estudantes."""

    if not (
        e_admin(request.user)
        or papel_utilizador(request.user) == Perfil.PAPEL_SECRETARIA
    ):
        raise PermissionDenied(
            "O painel de indicadores é reservado à secretaria e à "
            "administração."
        )

    periodo = request.GET.get("periodo") or PERIODO_PAINEL_PREDEFINIDO
    if periodo not in dict(PERIODOS_PAINEL):
        periodo = PERIODO_PAINEL_PREDEFINIDO

    inicio = _inicio_periodo_painel(periodo)
    pedidos = Pedido.objects.all()
    if inicio is not None:
        pedidos = pedidos.filter(criado_em__gte=inicio)

    contagens_estado = {
        linha["estado"]: linha["total"]
        for linha in pedidos.values("estado").annotate(total=Count("pk"))
    }
    cartoes = {
        "total": pedidos.count(),
        "em_tratamento": contagens_estado.get(
            Pedido.ESTADO_EM_TRATAMENTO,
            0,
        ),
        "prontos": contagens_estado.get(Pedido.ESTADO_PRONTO, 0),
        "entregues": contagens_estado.get(Pedido.ESTADO_ENTREGUE, 0),
        "indeferidos": contagens_estado.get(
            Pedido.ESTADO_INDEFERIDO,
            0,
        ),
    }

    por_tipo = list(
        pedidos.values("tipo__nome")
        .annotate(total=Count("pk"))
        .order_by("-total", "tipo__nome")
    )
    grafico_tipos = {
        "labels": [linha["tipo__nome"] for linha in por_tipo],
        "valores": [linha["total"] for linha in por_tipo],
    }
    grafico_estados = _dados_grafico_estados(
        contagens_estado,
        Pedido.ESTADO_CHOICES,
    )

    contagens_fila_etapa = {
        linha["etapa_actual"]: linha["total"]
        for linha in Pedido.objects.filter(
            estado=Pedido.ESTADO_EM_TRATAMENTO,
        )
        .values("etapa_actual")
        .annotate(total=Count("pk"))
    }
    grafico_fila = _dados_grafico_estados(
        contagens_fila_etapa,
        Pedido.ETAPA_CHOICES,
    )

    indeferidos = Decisao.objects.filter(
        resultado=Decisao.RESULTADO_INDEFERIDO,
    )
    if inicio is not None:
        indeferidos = indeferidos.filter(data_hora__gte=inicio)
    contagens_indeferidos = {
        linha["etapa"]: linha["total"]
        for linha in indeferidos.values("etapa").annotate(total=Count("pk"))
    }
    grafico_indeferidos = _dados_grafico_estados(
        contagens_indeferidos,
        Pedido.ETAPA_CHOICES,
    )

    duracao = ExpressionWrapper(
        F("pronto_em") - F("criado_em"),
        output_field=DurationField(),
    )
    concluidos = Pedido.objects.filter(
        estado__in=(Pedido.ESTADO_PRONTO, Pedido.ESTADO_ENTREGUE),
        pronto_em__isnull=False,
    )
    if inicio is not None:
        concluidos = concluidos.filter(
            Q(pronto_em__gte=inicio) | Q(entregue_em__gte=inicio)
        )
    medias = {
        linha["tipo_id"]: linha["media"]
        for linha in concluidos.values("tipo_id").annotate(media=Avg(duracao))
    }

    tempo_medio = []
    for tipo in TipoDocumento.objects.order_by("nome"):
        media = medias.get(tipo.pk)
        media_dias = (
            round(media.total_seconds() / 86400, 1)
            if media is not None
            else None
        )
        prazo = tipo.prazo_estimado_dias
        tempo_medio.append(
            {
                "tipo": tipo,
                "media_dias": media_dias,
                "prazo_dias": prazo,
                "excede": bool(
                    media_dias is not None
                    and prazo
                    and media_dias > prazo
                ),
            }
        )

    mais_antigos = (
        Pedido.objects.filter(estado=Pedido.ESTADO_EM_TRATAMENTO)
        .select_related("tipo")
        .order_by("criado_em")[:10]
    )

    contexto = {
        "periodo": periodo,
        "periodos": PERIODOS_PAINEL,
        "cartoes": cartoes,
        "grafico_tipos": grafico_tipos,
        "grafico_estados": grafico_estados,
        "grafico_fila": grafico_fila,
        "grafico_indeferidos": grafico_indeferidos,
        "tempo_medio": tempo_medio,
        "mais_antigos": mais_antigos,
    }
    return render(request, "pedidos/painel.html", contexto)


@login_required
@staff_required
def pedido_staff_detalhe(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("estudante__perfil", "tipo"),
        pk=pk,
    )

    papel = papel_utilizador(request.user)
    admin = e_admin(request.user)

    if not admin and papel != Perfil.PAPEL_SECRETARIA:
        etapa_do_papel = {
            Perfil.PAPEL_CREDITO: Pedido.ETAPA_CREDITO,
            Perfil.PAPEL_REGISTO: Pedido.ETAPA_REGISTO,
        }.get(papel)
        if pedido.etapa_actual != etapa_do_papel:
            raise Http404("Pedido não encontrado.")

    anexos = pedido.anexos.select_related("carregado_por")
    decisoes = pedido.decisoes.select_related("decidido_por")
    comprovativo = next(
        (anexo for anexo in anexos if anexo.tipo == Anexo.TIPO_COMPROVATIVO),
        None,
    )

    pode = services.pode_decidir(request.user, pedido)
    em_tratamento = pedido.estado == Pedido.ESTADO_EM_TRATAMENTO
    etapa_actual = pedido.etapa_actual

    contexto = {
        "pedido": pedido,
        "anexos": anexos,
        "decisoes": decisoes,
        "comprovativo": comprovativo,
        "pode_aprovar": (
            pode
            and em_tratamento
            and etapa_actual in services.ETAPAS_APROVACAO
        ),
        "pode_indeferir": pode and em_tratamento,
        "pode_marcar_pronto": (
            pode
            and em_tratamento
            and etapa_actual == Pedido.ETAPA_SECRETARIA_FINAL
        ),
        "pode_marcar_entregue": (
            pode and pedido.estado == Pedido.ESTADO_PRONTO
        ),
        "pode_carregar_extracto": (
            (admin or papel == Perfil.PAPEL_CREDITO)
            and em_tratamento
            and etapa_actual == Pedido.ETAPA_CREDITO
        ),
        "mostrar_valor_credito": (
            (admin or papel == Perfil.PAPEL_CREDITO)
            and etapa_actual == Pedido.ETAPA_CREDITO
        ),
    }
    return render(request, "pedidos/pedido_staff_detalhe.html", contexto)


def _mensagem_erro(erro):
    if hasattr(erro, "messages") and erro.messages:
        return " ".join(erro.messages)
    return str(erro)


def _voltar_ao_detalhe(pedido):
    return redirect("pedidos:pedido_staff_detalhe", pk=pedido.pk)


@login_required
@staff_required
@require_POST
def aprovar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    try:
        services.aprovar(
            pedido,
            request.user,
            request.POST.get("justificacao") or "",
        )
    except ValidationError as erro:
        messages.error(request, _mensagem_erro(erro))
    else:
        messages.success(request, "Pedido aprovado e encaminhado.")
    return _voltar_ao_detalhe(pedido)


@login_required
@staff_required
@require_POST
def indeferir(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    try:
        services.indeferir(
            pedido,
            request.user,
            request.POST.get("motivo") or "",
        )
    except ValidationError as erro:
        messages.error(request, _mensagem_erro(erro))
    else:
        messages.success(request, "Pedido indeferido.")
    return _voltar_ao_detalhe(pedido)


@login_required
@staff_required
@require_POST
def marcar_pronto(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    try:
        services.marcar_pronto(pedido, request.user)
    except ValidationError as erro:
        messages.error(request, _mensagem_erro(erro))
    else:
        messages.success(request, "Pedido marcado como pronto.")
    return _voltar_ao_detalhe(pedido)


@login_required
@staff_required
@require_POST
def marcar_entregue(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    try:
        services.marcar_entregue(pedido, request.user)
    except ValidationError as erro:
        messages.error(request, _mensagem_erro(erro))
    else:
        messages.success(request, "Entrega registada.")
    return _voltar_ao_detalhe(pedido)


@login_required
@staff_required
@require_POST
def carregar_extracto(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    papel = papel_utilizador(request.user)

    if not (e_admin(request.user) or papel == Perfil.PAPEL_CREDITO):
        raise PermissionDenied(
            "Só o controlo de crédito pode carregar extractos."
        )

    if (
        pedido.estado != Pedido.ESTADO_EM_TRATAMENTO
        or pedido.etapa_actual != Pedido.ETAPA_CREDITO
    ):
        raise Http404("Pedido não encontrado.")

    ficheiro = request.FILES.get("ficheiro") or request.FILES.get("extracto")
    if not ficheiro:
        messages.error(request, "Escolha o ficheiro do extracto.")
        return _voltar_ao_detalhe(pedido)

    try:
        validar_anexo(ficheiro)
    except ValidationError as erro:
        messages.error(request, _mensagem_erro(erro))
        return _voltar_ao_detalhe(pedido)

    Anexo.objects.create(
        pedido=pedido,
        tipo=Anexo.TIPO_EXTRACTO,
        ficheiro=ficheiro,
        nome_original=ficheiro.name,
        visivel_ao_estudante=False,
        carregado_por=request.user,
    )
    messages.success(request, "Extracto carregado com sucesso.")
    return _voltar_ao_detalhe(pedido)
