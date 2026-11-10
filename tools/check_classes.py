#!/usr/bin/env python3
"""Verifica se todos os tokens de class="" dos templates existem no CSS compilado.

Extrai todos os tokens de classe dos ficheiros HTML em templates/ e compara com
as classes definidas em static/css/app.css. Classes de componentes próprios
(definidas em static/css/input.css) e classes do Unpoly são consideradas
válidas mesmo que não apareçam como seletores simples no CSS compilado.
"""

import re
import sys
from pathlib import Path

TEMPLATES_DIR = Path("templates")
CSS_FILE = Path("static/css/app.css")

# Classes de componentes próprios definidas em static/css/input.css
COMPONENT_CLASSES = {
    "btn", "btn-primary", "btn-secondary", "btn-ghost", "btn-danger", "btn-sm",
    "card", "card-header", "card-body", "card-footer",
    "status-pill", "status-novo", "status-credito", "status-registo",
    "status-assinatura", "status-pronto", "status-indeferido",
    "stat-tile", "stat-tile-number", "stat-tile-label",
    "form-field", "form-label", "form-input", "form-select", "form-textarea",
    "form-hint", "form-error", "form-file",
    "data-table",
    "empty-state", "empty-state-icon",
    "page-header", "page-title", "page-subtitle", "breadcrumb",
    "breadcrumb-separator",
    "icon",
    "toast", "toast-container", "toast-success", "toast-error", "toast-warning",
    "toast-info", "toast-dismiss",
    # Variantes responsivas do Tailwind v4 (geradas dentro de media queries)
    "sm:px-6", "lg:px-8", "sm:px-4",
}

UNPOLY_CLASSES = {
    "up-can-clean", "up-destroying", "up-insertion", "up-placeholder",
    "up-modal", "up-modal-backdrop", "up-modal-viewport", "up-modal-dialog",
    "up-modal-content", "up-modal-close", "up-popup", "up-popup-content",
    "up-tooltip", "up-tooltip-content", "up-current", "up-active",
    "up-anchored", "up-fixed", "up-bounds",
}

IGNORE_TOKENS = {
    "h-", "w-", "toast-", "bg-", "text-", "p-", "px-", "py-", "mt-", "mb-",
    "mr-", "ml-", "rounded-", "border-", "focus-", "hover-",
    "alert", "error", "info", "success", "warning",
}


def remove_django_expressions(texto):
    texto = re.sub(r"\{%.*?%\}", " ", texto)
    texto = re.sub(r"\{\{.*?\}\}", " ", texto)
    texto = re.sub(r"\{#.*?#\}", " ", texto)
    return texto


def extrai_classes_templates():
    classes = set()
    for ficheiro in TEMPLATES_DIR.rglob("*.html"):
        conteudo = ficheiro.read_text(encoding="utf-8")
        for match in re.finditer(r'class="([^"]*)"', conteudo):
            classe_bruta = match.group(1)
            classe_limpa = remove_django_expressions(classe_bruta)
            for token in classe_limpa.split():
                token = token.strip()
                if token and token not in IGNORE_TOKENS:
                    classes.add(token)
    return classes


def extrai_classes_css():
    conteudo = CSS_FILE.read_text(encoding="utf-8")
    classes = set()
    for match in re.finditer(r'\.([a-zA-Z0-9_:\-\\\/\[\]]+)', conteudo):
        nome = match.group(1).replace("\\", "")
        classes.add(nome)
    return classes


def eh_valor_arbitrario(classe):
    return "[" in classe or "/" in classe or re.search(r'\d+\.\d+', classe) is not None


def classe_valida(classe, classes_css):
    if classe in COMPONENT_CLASSES:
        return True
    if classe in UNPOLY_CLASSES:
        return True
    if classe in classes_css:
        return True
    if eh_valor_arbitrario(classe):
        return True
    # Variantes do Tailwind (ex.: lg:pl-64, hover:bg-slate-100, md:\:open)
    # No CSS do Tailwind v4, a variante vem ANTES da classe base com pseudo-elemento
    # (ex.: .hover\:text-rose-800:hover em vez de .hover\:text-rose-800)
    if ":" in classe:
        if classe in classes_css:
            return True
        classe_limpa = classe.replace("\\:", ":")
        for css_classe in classes_css:
            if css_classe.startswith(classe_limpa):
                return True
        partes = classe.split(":")
        classe_base = partes[-1].replace("\\:", ":")
        if classe_base in classes_css or classe_base in COMPONENT_CLASSES:
            return True
        for parte in partes:
            parte_limpa = parte.replace("\\:", ":")
            if parte_limpa in classes_css or parte_limpa in COMPONENT_CLASSES:
                return True
        # Para breakpoints responsivos (sm:, md:, lg:, xl:), verificar a classe utilitária
        breakpoints = {"sm", "md", "lg", "xl", "2xl"}
        if partes[0] in breakpoints:
            sufixo = ":".join(partes[1:]).replace("\\:", ":")
            if sufixo in classes_css or sufixo in COMPONENT_CLASSES:
                return True
    return False


def main():
    classes_templates = extrai_classes_templates()
    classes_css = extrai_classes_css()

    invalidas = []
    for classe in sorted(classes_templates):
        if not classe_valida(classe, classes_css):
            invalidas.append(classe)

    print(f"Classes encontradas nos templates: {len(classes_templates)}")
    print(f"Classes definidas no CSS: {len(classes_css)}")
    print(f"Classes inválidas: {len(invalidas)}")

    if invalidas:
        print("\nClasses NÃO encontradas no CSS nem como componentes próprios:")
        for classe in invalidas:
            print(f"  - {classe}")
        return 1

    print("\nTodas as classes são válidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
