from django.conf import settings


def google_oauth(request):
    """Só mostra o botão Google quando as credenciais estão configuradas."""
    return {
        "google_oauth_enabled": bool(
            getattr(settings, "GOOGLE_CLIENT_ID", "")
            and getattr(settings, "GOOGLE_CLIENT_SECRET", "")
        )
    }


def atendimento_presencial(request):
    """Textos de apoio para situações que exigem atendimento presencial."""
    return {
        "atendimento_presencial_info": getattr(
            settings,
            "ATENDIMENTO_PRESENCIAL_INFO",
            "Dirige-te à Secretaria da Faculdade e faz o pedido "
            "presencialmente.",
        ),
        "curso_nao_encontrado_texto": (
            "Não encontras o teu curso na lista?"
        ),
    }
