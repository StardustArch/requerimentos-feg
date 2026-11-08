from django.core.management.base import BaseCommand

from contas.dados_cursos import CURSOS_POR_GRAU
from contas.models import Curso


class Command(BaseCommand):
    help = (
        "Cria o catálogo de cursos da faculdade. O comando é idempotente: "
        "cursos com o mesmo nome e grau não são duplicados."
    )

    def handle(self, *args, **options):
        criados = 0

        for grau, nomes in CURSOS_POR_GRAU:
            for nome in nomes:
                _, criado = Curso.objects.get_or_create(
                    nome=nome,
                    grau=grau,
                )
                if criado:
                    criados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Cursos: {criados} criado(s); {Curso.objects.count()} no total."
            )
        )
        for grau, etiqueta in Curso.GRAU_CHOICES:
            existentes = Curso.objects.filter(grau=grau).count()
            self.stdout.write(f"  {etiqueta}: {existentes}")
