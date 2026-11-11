"""Widget de upload de ficheiro com estilo UCM-FEG.

Renderiza um input real (visualmente oculto, mas acessível) cujo label se
comporta como um botão secondary "Escolher ficheiro", com o nome do ficheiro
seleccionado ao lado. O nome é actualizado através de um pequeno
up.compiler do Unpoly.
"""

from django.forms.widgets import FileInput
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class StyledFileInput(FileInput):
    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs.setdefault("type", "file")
        attrs.setdefault("accept", self.attrs.get("accept", ""))
        if self.attrs.get("required"):
            attrs["required"] = "required"
        input_id = attrs.get("id") or f"id_{name}"

        current_name = value.name if value and hasattr(value, "name") else ""

        contexto = {
            "input_id": input_id,
            "name": name,
            "accept": attrs["accept"],
            "required": 'required' if attrs.get("required") else "",
            "aria_label": attrs.get("aria-label", ""),
            "current_name": current_name,
        }
        html = render_to_string("widgets/styled_file_input.html", contexto)
        return mark_safe(html)
