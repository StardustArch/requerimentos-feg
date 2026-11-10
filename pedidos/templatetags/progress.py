"""Tags de template para a barra de progresso por pedido."""

from django import template
from django.template.loader import render_to_string

register = template.Library()


@register.simple_tag
def progress_bar(pedido, variant="compact"):
    """Renderiza a barra de progresso de um pedido.

    Uso: {% progress_bar pedido "compact" %} ou {% progress_bar pedido "full" %}
    """
    progresso = pedido.progresso
    return render_to_string(
        "components/progress_steps.html",
        {"progresso": progresso, "variant": variant},
    )
