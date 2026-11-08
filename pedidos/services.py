"""Regras de negócio do fluxo de decisão dos pedidos.

Toda a lógica de transição de etapas e de registo de decisões vive aqui. As
vistas limitam-se a validar a entrada do utilizador e a chamar estes serviços.
"""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from contas.models import Perfil
from contas.permissoes import e_admin, papel_utilizador

from .models import Decisao, Pedido
from .notificacoes import notificar_estudante

ETAPAS_APROVACAO = (
    Pedido.ETAPA_SECRETARIA_RECEPCAO,
    Pedido.ETAPA_CREDITO,
    Pedido.ETAPA_REGISTO,
)

PAPEIS_POR_ETAPA = {
    Pedido.ETAPA_SECRETARIA_RECEPCAO: Perfil.PAPEL_SECRETARIA,
    Pedido.ETAPA_CREDITO: Perfil.PAPEL_CREDITO,
    Pedido.ETAPA_REGISTO: Perfil.PAPEL_REGISTO,
    Pedido.ETAPA_SECRETARIA_FINAL: Perfil.PAPEL_SECRETARIA,
}


def pode_decidir(user, pedido):
    """Indica se o utilizador pode decidir o pedido na etapa actual."""

    if e_admin(user):
        return True

    papel = papel_utilizador(user)
    if papel is None:
        return False

    return PAPEIS_POR_ETAPA.get(pedido.etapa_actual) == papel


def _bloquear(pedido):
    return (
        Pedido.objects.select_for_update()
        .select_related("tipo", "estudante", "estudante__perfil")
        .get(pk=pedido.pk)
    )


def _exigir_permissao(pedido, actor):
    if not pode_decidir(actor, pedido):
        raise PermissionDenied(
            "Não tem permissão para decidir este pedido nesta etapa."
        )


def _exigir_em_tratamento(pedido):
    if pedido.estado != Pedido.ESTADO_EM_TRATAMENTO:
        raise ValidationError(
            "Só é possível decidir pedidos em tratamento."
        )


def _registar_decisao(pedido, actor, resultado, justificacao=""):
    return Decisao.objects.create(
        pedido=pedido,
        etapa=pedido.etapa_actual,
        resultado=resultado,
        justificacao=justificacao,
        decidido_por=actor,
    )


def _agendar_notificacao(pedido, evento):
    transaction.on_commit(
        lambda: notificar_estudante(pedido, evento)
    )


def aprovar(pedido, actor, justificacao=""):
    """Aprova a etapa actual e avança o pedido para a etapa seguinte."""

    with transaction.atomic():
        pedido = _bloquear(pedido)
        _exigir_permissao(pedido, actor)
        _exigir_em_tratamento(pedido)

        if pedido.etapa_actual not in ETAPAS_APROVACAO:
            raise ValidationError(
                "O pedido não pode ser aprovado na etapa actual."
            )

        etapa = pedido.etapa_actual
        if etapa == Pedido.ETAPA_SECRETARIA_RECEPCAO:
            proxima_etapa = Pedido.ETAPA_CREDITO
        elif etapa == Pedido.ETAPA_CREDITO:
            if pedido.tipo.passa_registo_academico:
                proxima_etapa = Pedido.ETAPA_REGISTO
            else:
                proxima_etapa = Pedido.ETAPA_SECRETARIA_FINAL
        else:
            proxima_etapa = Pedido.ETAPA_SECRETARIA_FINAL

        _registar_decisao(
            pedido,
            actor,
            Decisao.RESULTADO_APROVADO,
            justificacao,
        )
        pedido.etapa_actual = proxima_etapa
        pedido.save(update_fields=["etapa_actual"])
        return pedido


def indeferir(pedido, actor, motivo):
    """Pára o pedido e regista o motivo do indeferimento."""

    motivo = (motivo or "").strip()
    if len(motivo) < 10:
        raise ValidationError(
            "O motivo do indeferimento é obrigatório e deve ter pelo menos "
            "10 caracteres."
        )

    with transaction.atomic():
        pedido = _bloquear(pedido)
        _exigir_permissao(pedido, actor)
        _exigir_em_tratamento(pedido)

        etapa = pedido.etapa_actual
        _registar_decisao(
            pedido,
            actor,
            Decisao.RESULTADO_INDEFERIDO,
            motivo,
        )
        pedido.estado = Pedido.ESTADO_INDEFERIDO
        pedido.motivo_indeferimento = motivo
        pedido.indeferido_na_etapa = etapa
        pedido.save(
            update_fields=[
                "estado",
                "motivo_indeferimento",
                "indeferido_na_etapa",
            ]
        )
        _agendar_notificacao(pedido, "indeferido")
        return pedido


def marcar_pronto(pedido, actor):
    """Marca o pedido como pronto para levantamento na secretaria."""

    with transaction.atomic():
        pedido = _bloquear(pedido)
        _exigir_permissao(pedido, actor)
        _exigir_em_tratamento(pedido)

        if pedido.etapa_actual != Pedido.ETAPA_SECRETARIA_FINAL:
            raise ValidationError(
                "Só é possível marcar como pronto na etapa da secretaria "
                "final."
            )

        _registar_decisao(
            pedido,
            actor,
            Decisao.RESULTADO_PRONTO,
        )
        pedido.estado = Pedido.ESTADO_PRONTO
        pedido.pronto_em = timezone.now()
        pedido.save(update_fields=["estado", "pronto_em"])
        _agendar_notificacao(pedido, "pronto")
        return pedido


def marcar_entregue(pedido, actor):
    """Regista a entrega física do documento ao estudante."""

    with transaction.atomic():
        pedido = _bloquear(pedido)
        _exigir_permissao(pedido, actor)

        if pedido.estado != Pedido.ESTADO_PRONTO:
            raise ValidationError(
                "Só é possível marcar como entregue um pedido pronto."
            )

        _registar_decisao(
            pedido,
            actor,
            Decisao.RESULTADO_ENTREGUE,
        )
        pedido.estado = Pedido.ESTADO_ENTREGUE
        pedido.entregue_em = timezone.now()
        pedido.entregue_por = actor
        pedido.save(
            update_fields=["estado", "entregue_em", "entregue_por"]
        )
        return pedido
