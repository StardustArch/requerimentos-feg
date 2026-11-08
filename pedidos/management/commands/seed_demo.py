import base64
import os
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from contas.models import Perfil
from pedidos.models import Anexo, Pedido, TipoDocumento

PASSWORD_DEMO = os.environ.get("DEMO_PASSWORD", "demo123")

# PNG 1x1 transparente, mínimo e válido.
PNG_MINIMO = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


def _pdf_minimo():
    """Constrói um PDF pequeno e válido, com a tabela xref correcta."""

    objetos = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] >>",
    )
    partes = [b"%PDF-1.4\n"]
    offsets = []

    for numero, objeto in enumerate(objetos, start=1):
        offsets.append(sum(len(parte) for parte in partes))
        partes.append(f"{numero} 0 obj\n".encode("ascii"))
        partes.append(objeto + b"\n")
        partes.append(b"endobj\n")

    inicio_xref = sum(len(parte) for parte in partes)
    partes.append(b"xref\n")
    partes.append(f"0 {len(objetos) + 1}\n".encode("ascii"))
    partes.append(b"0000000000 65535 f \n")
    for offset in offsets:
        partes.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    partes.append(b"trailer\n")
    partes.append(
        f"<< /Size {len(objetos) + 1} /Root 1 0 R >>\n".encode("ascii")
    )
    partes.append(f"startxref\n{inicio_xref}\n%%EOF\n".encode("ascii"))
    return b"".join(partes)


TIPOS_DOCUMENTO = (
    {
        "nome": "Declaração simples",
        "taxa_licenciatura": Decimal("100"),
        "taxa_mestrado": Decimal("200"),
        "taxa_doutoramento": Decimal("300"),
        "passa_registo_academico": False,
        "prazo_estimado_dias": None,
    },
    {
        "nome": "Declaração de notas",
        "taxa_licenciatura": Decimal("200"),
        "taxa_mestrado": Decimal("300"),
        "taxa_doutoramento": Decimal("400"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": None,
    },
    {
        "nome": "Certificado normal",
        "taxa_licenciatura": Decimal("2500"),
        "taxa_mestrado": Decimal("5000"),
        "taxa_doutoramento": Decimal("10000"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": 15,
    },
    {
        "nome": "Certificado normal (2.ª via)",
        "taxa_licenciatura": Decimal("5000"),
        "taxa_mestrado": Decimal("7500"),
        "taxa_doutoramento": Decimal("12500"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": 15,
    },
    {
        "nome": "Certificado urgente",
        "taxa_licenciatura": Decimal("5000"),
        "taxa_mestrado": Decimal("10000"),
        "taxa_doutoramento": Decimal("20000"),
        "passa_registo_academico": True,
        "prazo_estimado_dias": 5,
    },
    {
        "nome": "Diploma normal",
        "taxa_licenciatura": Decimal("2000"),
        "taxa_mestrado": Decimal("3000"),
        "taxa_doutoramento": Decimal("10000"),
        "passa_registo_academico": False,
        "prazo_estimado_dias": 15,
    },
    {
        "nome": "Conteúdos programáticos",
        "taxa_licenciatura": Decimal("700"),
        "taxa_mestrado": Decimal("1400"),
        "taxa_doutoramento": Decimal("2100"),
        "passa_registo_academico": False,
        "prazo_estimado_dias": None,
    },
)

UTILIZADORES_DEMO = (
    {
        "username": "admin",
        "email": "admin@ucm.ac.mz",
        "papel": Perfil.PAPEL_ADMIN,
        "superuser": True,
    },
    {
        "username": "secretaria1",
        "email": "secretaria1@ucm.ac.mz",
        "papel": Perfil.PAPEL_SECRETARIA,
        "superuser": False,
    },
    {
        "username": "credito1",
        "email": "credito1@ucm.ac.mz",
        "papel": Perfil.PAPEL_CREDITO,
        "superuser": False,
    },
    {
        "username": "registo1",
        "email": "registo1@ucm.ac.mz",
        "papel": Perfil.PAPEL_REGISTO,
        "superuser": False,
    },
    {
        "username": "estudante1",
        "email": "estudante1@estudante.ucm.ac.mz",
        "papel": Perfil.PAPEL_ESTUDANTE,
        "superuser": False,
        "numero_estudante": "2023001234",
        "curso": "Informática de Gestão",
        "grau": Perfil.GRAU_LICENCIATURA,
    },
)

PEDIDOS_DEMO = (
    {
        "motivo": "Pedido de demonstração — certificado normal na secretaria.",
        "tipo": "Certificado normal",
        "estado": Pedido.ESTADO_EM_TRATAMENTO,
        "etapa": Pedido.ETAPA_SECRETARIA_RECEPCAO,
        "motivo_indeferimento": "",
    },
    {
        "motivo": "Pedido de demonstração — declaração de notas no crédito.",
        "tipo": "Declaração de notas",
        "estado": Pedido.ESTADO_EM_TRATAMENTO,
        "etapa": Pedido.ETAPA_CREDITO,
        "motivo_indeferimento": "",
    },
    {
        "motivo": "Pedido de demonstração — declaração simples indeferida.",
        "tipo": "Declaração simples",
        "estado": Pedido.ESTADO_INDEFERIDO,
        "etapa": Pedido.ETAPA_SECRETARIA_RECEPCAO,
        "motivo_indeferimento": (
            "O comprovativo de pagamento está ilegível. Submeta novamente o "
            "pedido com um comprovativo válido."
        ),
    },
)


class Command(BaseCommand):
    help = "Cria os tipos de documento e as contas de demonstração."

    def handle(self, *args, **options):
        tipos_criados = 0
        tipos_existentes = 0
        utilizadores_criados = 0
        utilizadores_existentes = 0
        pedidos_criados = 0
        pedidos_existentes = 0
        anexos_criados = 0

        for dados in TIPOS_DOCUMENTO:
            _, criado = TipoDocumento.objects.update_or_create(
                nome=dados["nome"],
                defaults={
                    "taxa_licenciatura": dados["taxa_licenciatura"],
                    "taxa_mestrado": dados["taxa_mestrado"],
                    "taxa_doutoramento": dados["taxa_doutoramento"],
                    "passa_registo_academico": dados["passa_registo_academico"],
                    "prazo_estimado_dias": dados["prazo_estimado_dias"],
                    "activo": True,
                },
            )
            if criado:
                tipos_criados += 1
            else:
                tipos_existentes += 1

        for dados in UTILIZADORES_DEMO:
            _, criado = self._garantir_utilizador(dados)
            if criado:
                utilizadores_criados += 1
            else:
                utilizadores_existentes += 1

        criados, existentes, anexos = self._garantir_pedidos()
        pedidos_criados += criados
        pedidos_existentes += existentes
        anexos_criados += anexos

        self.stdout.write(self.style.SUCCESS("Dados de demonstração prontos."))
        self.stdout.write(
            "Tipos de documento: {criados} criados, {existentes} já existiam".format(
                criados=tipos_criados,
                existentes=tipos_existentes,
            )
        )
        self.stdout.write(
            "Utilizadores: {criados} criados, {existentes} já existiam".format(
                criados=utilizadores_criados,
                existentes=utilizadores_existentes,
            )
        )
        self.stdout.write(
            "Pedidos: {criados} criados, {existentes} já existiam; "
            "anexos: {anexos} criados".format(
                criados=pedidos_criados,
                existentes=pedidos_existentes,
                anexos=anexos_criados,
            )
        )

        if PASSWORD_DEMO == "demo123":
            self.stdout.write(
                self.style.WARNING(
                    "AVISO: a palavra-passe de demonstração está a usar o valor "
                    "por defeito (demo123). Defina a variável de ambiente "
                    "DEMO_PASSWORD em produção."
                )
            )

    def _garantir_pedidos(self):
        estudante = User.objects.get(username="estudante1")
        pedidos_criados = 0
        pedidos_existentes = 0
        anexos_criados = 0
        pdf_demo = _pdf_minimo()

        for dados in PEDIDOS_DEMO:
            tipo = TipoDocumento.objects.get(nome=dados["tipo"])
            pedido, criado = Pedido.objects.get_or_create(
                estudante=estudante,
                motivo=dados["motivo"],
                defaults={
                    "tipo": tipo,
                    "grau": estudante.perfil.grau,
                    "estado": dados["estado"],
                    "etapa_actual": dados["etapa"],
                    "motivo_indeferimento": dados["motivo_indeferimento"],
                },
            )
            if criado:
                pedidos_criados += 1
            else:
                pedidos_existentes += 1

            anexos = (
                (
                    Anexo.TIPO_BI,
                    f"bi_demo_{pedido.pk}.pdf",
                    pdf_demo,
                    "bi_demo.pdf",
                ),
                (
                    Anexo.TIPO_COMPROVATIVO,
                    f"comprovativo_demo_{pedido.pk}.png",
                    PNG_MINIMO,
                    "comprovativo_demo.png",
                ),
            )

            for tipo_anexo, nome_ficheiro, conteudo, nome_original in anexos:
                if pedido.anexos.filter(tipo=tipo_anexo).exists():
                    continue
                Anexo.objects.create(
                    pedido=pedido,
                    tipo=tipo_anexo,
                    ficheiro=ContentFile(conteudo, name=nome_ficheiro),
                    nome_original=nome_original,
                    visivel_ao_estudante=True,
                    carregado_por=estudante,
                )
                anexos_criados += 1

        return pedidos_criados, pedidos_existentes, anexos_criados

    def _garantir_utilizador(self, dados):
        utilizador, criado = User.objects.get_or_create(
            username=dados["username"],
            defaults={
                "email": dados["email"],
                "is_staff": dados["superuser"],
                "is_superuser": dados["superuser"],
            },
        )

        alterado = False
        if criado:
            utilizador.set_password(PASSWORD_DEMO)
            alterado = True

        if not utilizador.email:
            utilizador.email = dados["email"]
            alterado = True

        if dados["superuser"] and (
            not utilizador.is_staff or not utilizador.is_superuser
        ):
            utilizador.is_staff = True
            utilizador.is_superuser = True
            alterado = True

        if alterado:
            utilizador.save()

        perfil, _ = Perfil.objects.get_or_create(user=utilizador)
        campos_alterados = []

        if perfil.papel != dados["papel"]:
            perfil.papel = dados["papel"]
            campos_alterados.append("papel")

        for campo in ("numero_estudante", "curso", "grau"):
            valor = dados.get(campo)
            if valor and not getattr(perfil, campo):
                setattr(perfil, campo, valor)
                campos_alterados.append(campo)

        if campos_alterados:
            perfil.save(update_fields=campos_alterados)

        return utilizador, criado
