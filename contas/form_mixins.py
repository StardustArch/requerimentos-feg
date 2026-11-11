"""Mixin e widgets de formulário com estilo padrão da UCM-FEG.

Aplica automaticamente as classes de `static/css/input.css` (@layer components)
aos campos dos formulários, sem tocar na lógica de negócio nem nos testes.
"""

from django import forms
from django.forms.widgets import (
    ClearableFileInput,
    FileInput,
    Select,
    TextInput,
    Textarea,
    EmailInput,
    PasswordInput,
    NumberInput,
    DateInput,
)


class StyledFormMixin:
    """Mix que atribui classes de estilo aos widgets dos campos.

    - TextInput/Email/Password/Number/Date  → form-input
    - Textarea                              → form-textarea (rows=4, resize vertical)
    - Select                                → form-select
    - FileInput/ClearableFileInput          → form-file (estilo de upload)
    """

    FIELD_WIDGET_CLASSES = {
        TextInput: "form-input",
        EmailInput: "form-input",
        PasswordInput: "form-input",
        NumberInput: "form-input",
        DateInput: "form-input",
        Select: "form-select",
        Textarea: "form-textarea",
        FileInput: "form-file",
        ClearableFileInput: "form-file",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            for widget_class, css_class in self.FIELD_WIDGET_CLASSES.items():
                if isinstance(widget, widget_class):
                    classes = widget.attrs.get("class", "")
                    classes = (classes + " " + css_class).strip()
                    widget.attrs["class"] = classes
                    break

            # Textarea: rows=4 e apenas resize vertical
            if isinstance(widget, Textarea):
                widget.attrs.setdefault("rows", "4")
                widget.attrs["style"] = "resize: vertical;"
