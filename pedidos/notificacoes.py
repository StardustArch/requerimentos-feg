"""Notificações por email ao estudante.

As falhas de envio são apenas registadas no log: uma decisão já tomada nunca
pode ser revertida por causa de um problema no servidor de email.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _levantamento_info():
    return getattr(
        settings,
        "LEVANTAMENTO_INFO",
        "na Secretaria da Faculdade",
    )


def _corpo_pronto(pedido):
    return (
        f"O seu pedido {pedido.protocolo} está pronto para levantamento.\n\n"
        f"Tipo de documento: {pedido.tipo.nome}\n"
        f"O documento pode ser levantado {_levantamento_info()}.\n\n"
        "Apresente este protocolo no momento do levantamento.\n"
        "Pedidos de Documentos · UCM-FEG"
    )


def _corpo_indeferido(pedido):
    return (
        f"O seu pedido {pedido.protocolo} foi indeferido.\n\n"
        f"Tipo de documento: {pedido.tipo.nome}\n"
        f"Motivo: {pedido.motivo_indeferimento}\n\n"
        "Pode submeter um novo pedido com a informação corrigida.\n"
        "Pedidos de Documentos · UCM-FEG"
    )


def notificar_estudante(pedido, evento):
    """Envia ao estudante a notificação do evento indicado.

    Devolve ``True`` quando o email é enviado e ``False`` quando não há email
    ou quando o envio falha. Nunca propaga a excepção de envio.
    """

    destinatario = (getattr(pedido.estudante, "email", "") or "").strip()
    if not destinatario:
        return False

    if evento == "pronto":
        assunto = f"Pedido {pedido.protocolo} pronto para levantamento"
        corpo = _corpo_pronto(pedido)
    elif evento == "indeferido":
        assunto = f"Pedido {pedido.protocolo} indeferido"
        corpo = _corpo_indeferido(pedido)
    else:
        raise ValueError(f"Evento de notificação desconhecido: {evento!r}")

    try:
        send_mail(
            assunto,
            corpo,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Falha ao enviar a notificação %r do pedido %s para %s.",
            evento,
            pedido.protocolo,
            destinatario,
        )
        return False

    return True
