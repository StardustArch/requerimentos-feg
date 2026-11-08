"""Validação dos anexos enviados pelos estudantes.

A validação não confia no Content-Type nem apenas na extensão: confirma os
primeiros bytes do ficheiro. Não são usadas bibliotecas externas.
"""

import os

from django.conf import settings
from django.core.exceptions import ValidationError

EXTENSOES_PERMITIDAS = {
    ".pdf": b"%PDF",
    ".jpg": b"\xff\xd8\xff",
    ".jpeg": b"\xff\xd8\xff",
    ".png": b"\x89PNG",
}


def _tamanho(ficheiro):
    tamanho = getattr(ficheiro, "size", None)
    if tamanho is not None:
        return tamanho

    posicao = ficheiro.tell()
    ficheiro.seek(0, os.SEEK_END)
    tamanho = ficheiro.tell()
    ficheiro.seek(posicao)
    return tamanho


def validar_anexo(ficheiro):
    """Valida extensão, tamanho e assinatura binária do ficheiro."""

    if not ficheiro:
        return

    nome = getattr(ficheiro, "name", "") or ""
    extensao = os.path.splitext(nome)[1].lower()

    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValidationError(
            "Formato não permitido. Envie um ficheiro PDF, JPG ou PNG."
        )

    limite_bytes = int(settings.MAX_ANEXO_MB) * 1024 * 1024
    if _tamanho(ficheiro) > limite_bytes:
        raise ValidationError(
            f"O ficheiro excede o limite de {settings.MAX_ANEXO_MB} MB."
        )

    posicao = ficheiro.tell()
    try:
        ficheiro.seek(0)
        cabecalho = ficheiro.read(8)
    finally:
        ficheiro.seek(posicao)

    assinatura = EXTENSOES_PERMITIDAS[extensao]
    if not cabecalho.startswith(assinatura):
        raise ValidationError(
            "O conteúdo do ficheiro não corresponde à extensão indicada."
        )
