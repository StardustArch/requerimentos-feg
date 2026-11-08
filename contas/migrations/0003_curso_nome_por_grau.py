from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contas", "0002_curso_e_numero_estudante"),
    ]

    operations = [
        migrations.AlterField(
            model_name="curso",
            name="nome",
            field=models.CharField(max_length=150),
        ),
        migrations.AddConstraint(
            model_name="curso",
            constraint=models.UniqueConstraint(
                fields=("nome", "grau"),
                name="unique_curso_nome_por_grau",
            ),
        ),
    ]
