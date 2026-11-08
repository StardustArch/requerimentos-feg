"""Cópia de segurança consistente da base SQLite e da pasta media/."""

import sqlite3
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.utils import timezone

PREFIXO_BACKUP = "backup-"
SUFIXO_BACKUP = ".zip"


def _tamanho_legivel(numero_bytes):
    tamanho = float(numero_bytes)
    for unidade in ("B", "KB", "MB", "GB"):
        if tamanho < 1024 or unidade == "GB":
            if unidade == "B":
                return f"{int(tamanho)} {unidade}"
            return f"{tamanho:.1f} {unidade}"
        tamanho /= 1024
    return f"{tamanho:.1f} GB"


class Command(BaseCommand):
    help = (
        "Cria um zip com uma cópia consistente da base SQLite e da pasta "
        "media/."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--manter",
            type=int,
            default=14,
            help=(
                "Número de backups a conservar (por omissão: 14). Os mais "
                "antigos são apagados."
            ),
        )

    def handle(self, *args, **options):
        manter = options["manter"]
        if manter < 1:
            raise CommandError("--manter tem de ser um número inteiro positivo.")

        pasta = Path(
            getattr(settings, "BACKUP_DIR", settings.BASE_DIR / "backups")
        )
        pasta.mkdir(parents=True, exist_ok=True)

        agora = timezone.localtime()
        nome = f"{PREFIXO_BACKUP}{agora:%Y%m%d-%H%M%S-%f}{SUFIXO_BACKUP}"
        caminho = pasta / nome

        with TemporaryDirectory(prefix="requerimentos-backup-") as temporaria:
            copia_base = Path(temporaria) / "db.sqlite3"
            self._copiar_base(copia_base)
            with zipfile.ZipFile(
                caminho,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
            ) as arquivo:
                arquivo.write(copia_base, arcname="db.sqlite3")
                self._adicionar_media(arquivo)

        backups = sorted(pasta.glob(f"{PREFIXO_BACKUP}*{SUFIXO_BACKUP}"))
        for antigo in backups[:-manter]:
            antigo.unlink()

        restantes = len(
            list(pasta.glob(f"{PREFIXO_BACKUP}*{SUFIXO_BACKUP}"))
        )
        tamanho = caminho.stat().st_size

        self.stdout.write(
            self.style.SUCCESS(
                f"Backup criado: {nome} ({_tamanho_legivel(tamanho)})."
            )
        )
        self.stdout.write(
            f"Backups guardados: {restantes} (limite: {manter})."
        )

    def _copiar_base(self, destino):
        configuracao = connections["default"].settings_dict
        if configuracao["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError(
                "O comando fazer_backup só suporta bases de dados SQLite."
            )

        nome = str(configuracao["NAME"] or "")
        usar_conexao_do_django = (
            nome in {"", ":memory:"} or nome.startswith("file:")
        )

        if usar_conexao_do_django:
            # A base de testes do Django vive numa base SQLite em memória
            # partilhada; a única ligação que a vê é a do próprio Django.
            ligacao = connections["default"]
            ligacao.ensure_connection()
            origem = ligacao.connection
        else:
            caminho_base = Path(nome)
            if not caminho_base.exists():
                raise CommandError(
                    f"Base de dados SQLite não encontrada: {caminho_base}"
                )
            origem = sqlite3.connect(str(caminho_base))

        try:
            copia = sqlite3.connect(str(destino))
            try:
                # sqlite3.Connection.backup produz uma cópia consistente,
                # mesmo que a base esteja a ser escrita.
                origem.backup(copia)
            finally:
                copia.close()
        finally:
            if not usar_conexao_do_django:
                origem.close()

    def _adicionar_media(self, arquivo):
        raiz = Path(settings.MEDIA_ROOT)
        arquivo.writestr("media/", "")

        if not raiz.exists():
            return

        for ficheiro in sorted(raiz.rglob("*")):
            if not ficheiro.is_file():
                continue
            destino = Path("media") / ficheiro.relative_to(raiz)
            arquivo.write(ficheiro, arcname=str(destino))
