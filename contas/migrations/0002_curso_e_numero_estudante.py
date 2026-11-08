import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q


def migrar_cursos_existentes(apps, schema_editor):
    """Converte o antigo texto livre de curso em registos de Curso."""
    Curso = apps.get_model("contas", "Curso")
    Perfil = apps.get_model("contas", "Perfil")
    db_alias = schema_editor.connection.alias

    perfis = (
        Perfil.objects.using(db_alias)
        .exclude(curso_antigo__isnull=True)
        .exclude(curso_antigo="")
    )
    for nome in perfis.values_list("curso_antigo", flat=True).distinct():
        Curso.objects.using(db_alias).get_or_create(
            nome=nome,
            defaults={"grau": "licenciatura"},
        )

    for perfil in perfis:
        perfil.curso = Curso.objects.using(db_alias).get(
            nome=perfil.curso_antigo
        )
        perfil.save(update_fields=["curso"])


def reverter_cursos_existentes(apps, schema_editor):
    Perfil = apps.get_model("contas", "Perfil")
    db_alias = schema_editor.connection.alias

    for perfil in Perfil.objects.using(db_alias).select_related("curso"):
        if perfil.curso_id:
            perfil.curso_antigo = perfil.curso.nome
            perfil.save(update_fields=["curso_antigo"])


def limpar_numeros_duplicados(apps, schema_editor):
    """Antes de criar a restrição única, deixa apenas o primeiro dono."""
    Perfil = apps.get_model("contas", "Perfil")
    db_alias = schema_editor.connection.alias
    vistos = set()

    for perfil in (
        Perfil.objects.using(db_alias)
        .exclude(numero_estudante__isnull=True)
        .exclude(numero_estudante="")
        .order_by("pk")
    ):
        if perfil.numero_estudante in vistos:
            perfil.numero_estudante = None
            perfil.save(update_fields=["numero_estudante"])
        else:
            vistos.add(perfil.numero_estudante)


class Migration(migrations.Migration):

    dependencies = [
        ("contas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Curso",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nome", models.CharField(max_length=150, unique=True)),
                (
                    "grau",
                    models.CharField(
                        choices=[
                            ("licenciatura", "Licenciatura"),
                            ("mestrado", "Mestrado"),
                            ("doutoramento", "Doutoramento"),
                        ],
                        max_length=20,
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "curso",
                "verbose_name_plural": "cursos",
                "ordering": ("grau", "nome"),
            },
        ),
        migrations.RenameField(
            model_name="perfil",
            old_name="curso",
            new_name="curso_antigo",
        ),
        migrations.AddField(
            model_name="perfil",
            name="curso",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="perfis",
                to="contas.curso",
            ),
        ),
        migrations.RunPython(
            migrar_cursos_existentes,
            reverter_cursos_existentes,
        ),
        migrations.RemoveField(
            model_name="perfil",
            name="curso_antigo",
        ),
        migrations.RunPython(
            limpar_numeros_duplicados,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="perfil",
            constraint=models.UniqueConstraint(
                condition=Q(numero_estudante__isnull=False)
                & ~Q(numero_estudante=""),
                fields=("numero_estudante",),
                name="unique_numero_estudante_quando_preenchido",
            ),
        ),
    ]
