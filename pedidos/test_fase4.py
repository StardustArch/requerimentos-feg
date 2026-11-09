import shutil
import sqlite3
import tempfile
import zipfile
from datetime import timedelta
from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contas.models import Curso, Perfil
from pedidos.models import Decisao, Pedido, TipoDocumento


def _utilizador(username, email, papel, password="teste12345"):
    utilizador = User.objects.create_user(
        username=username,
        email=email,
        password=password,
    )
    Perfil.objects.filter(user=utilizador).update(papel=papel)
    return utilizador


class PainelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username="admin_painel",
            email="admin.painel@ucm.ac.mz",
            password="teste12345",
        )
        cls.secretaria = _utilizador(
            "secretaria_painel",
            "secretaria.painel@ucm.ac.mz",
            Perfil.PAPEL_SECRETARIA,
        )
        cls.credito = _utilizador(
            "credito_painel",
            "credito.painel@ucm.ac.mz",
            Perfil.PAPEL_CREDITO,
        )
        cls.registo = _utilizador(
            "registo_painel",
            "registo.painel@ucm.ac.mz",
            Perfil.PAPEL_REGISTO,
        )
        cls.estudante = _utilizador(
            "aluno_painel",
            "701111111@estudante.ucm.ac.mz",
            Perfil.PAPEL_ESTUDANTE,
        )
        cls.estudante.first_name = "NomePrivado"
        cls.estudante.last_name = "ApelidoPrivado"
        cls.estudante.save(update_fields=["first_name", "last_name"])
        curso = Curso.objects.create(
            nome="Curso do Painel",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        perfil = cls.estudante.perfil
        perfil.curso = curso
        perfil.grau = curso.grau
        perfil.save(update_fields=["curso", "grau"])

        cls.tipo = TipoDocumento.objects.create(
            nome="Certificado do painel",
            taxa_licenciatura=Decimal("100"),
            taxa_mestrado=Decimal("200"),
            taxa_doutoramento=Decimal("300"),
            prazo_estimado_dias=10,
        )
        cls.tipo_sem_prazo = TipoDocumento.objects.create(
            nome="Declaração do painel",
            taxa_licenciatura=Decimal("50"),
            taxa_mestrado=Decimal("100"),
            taxa_doutoramento=Decimal("150"),
        )

        agora = timezone.now()

        def criar(estado, criado_em, pronto_em=None, entregue_em=None):
            pedido = Pedido.objects.create(
                estudante=cls.estudante,
                tipo=cls.tipo,
                grau=cls.estudante.perfil.grau,
                motivo="Pedido de teste do painel.",
            )
            Pedido.objects.filter(pk=pedido.pk).update(
                estado=estado,
                criado_em=criado_em,
                pronto_em=pronto_em,
                entregue_em=entregue_em,
            )
            pedido.refresh_from_db()
            return pedido

        cls.pronto = criar(
            Pedido.ESTADO_PRONTO,
            agora - timedelta(days=20),
            pronto_em=agora - timedelta(days=8),
        )
        cls.entregue = criar(
            Pedido.ESTADO_ENTREGUE,
            agora - timedelta(days=25),
            pronto_em=agora - timedelta(days=7),
            entregue_em=agora - timedelta(days=6),
        )
        cls.em_tratamento = criar(
            Pedido.ESTADO_EM_TRATAMENTO,
            agora - timedelta(days=5),
        )
        cls.indeferido = criar(
            Pedido.ESTADO_INDEFERIDO,
            agora - timedelta(days=2),
        )
        Pedido.objects.filter(pk=cls.indeferido.pk).update(
            indeferido_na_etapa=Pedido.ETAPA_CREDITO,
            motivo_indeferimento="Documento de teste indeferido.",
        )
        Decisao.objects.create(
            pedido=cls.indeferido,
            etapa=Pedido.ETAPA_CREDITO,
            resultado=Decisao.RESULTADO_INDEFERIDO,
            justificacao="Documento de teste indeferido.",
            decidido_por=cls.admin,
        )
        cls.antigo = criar(
            Pedido.ESTADO_PRONTO,
            agora - timedelta(days=90),
            pronto_em=agora - timedelta(days=80),
        )

    def test_painel_so_abre_a_secretaria_e_ao_admin(self):
        url = reverse("painel")

        self.client.logout()
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse("contas:login")))

        for utilizador in (self.credito, self.registo, self.estudante):
            with self.subTest(utilizador=utilizador.username):
                self.client.force_login(utilizador)
                self.assertEqual(self.client.get(url).status_code, 403)

        for utilizador in (self.secretaria, self.admin):
            with self.subTest(utilizador=utilizador.username):
                self.client.force_login(utilizador)
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_totais_e_tempo_medio_batem_com_os_dados_criados(self):
        self.client.force_login(self.secretaria)
        resposta = self.client.get(reverse("painel"))

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.context["cartoes"],
            {
                "total": 4,
                "em_tratamento": 1,
                "prontos": 1,
                "entregues": 1,
                "indeferidos": 1,
            },
        )

        linha = next(
            item
            for item in resposta.context["tempo_medio"]
            if item["tipo"] == self.tipo
        )
        self.assertEqual(linha["media_dias"], 15.0)
        self.assertEqual(linha["prazo_dias"], 10)
        self.assertTrue(linha["excede"])

        sem_prazo = next(
            item
            for item in resposta.context["tempo_medio"]
            if item["tipo"] == self.tipo_sem_prazo
        )
        self.assertIsNone(sem_prazo["media_dias"])
        self.assertIsNone(sem_prazo["prazo_dias"])

    def test_filtro_de_periodo_invalido_e_ignorado_sem_erro_500(self):
        self.client.force_login(self.secretaria)
        url = reverse("painel")

        resposta = self.client.get(url, {"periodo": "valor-invalido"})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["periodo"], "30d")
        self.assertEqual(resposta.context["cartoes"]["total"], 4)

        resposta = self.client.get(url, {"periodo": "tudo"})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["periodo"], "tudo")
        self.assertEqual(resposta.context["cartoes"]["total"], 5)

    def test_painel_nao_mostra_nomes_nem_emails_de_estudantes(self):
        self.client.force_login(self.secretaria)
        resposta = self.client.get(reverse("painel"))

        self.assertNotContains(resposta, self.estudante.first_name)
        self.assertNotContains(resposta, self.estudante.last_name)
        self.assertNotContains(resposta, self.estudante.email)
        self.assertNotContains(resposta, self.estudante.username)
        self.assertNotContains(resposta, self.estudante.perfil.numero_estudante)


class BackupTests(TransactionTestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp(prefix="requerimentos-backup-teste-"))
        self.addCleanup(shutil.rmtree, self.pasta, ignore_errors=True)
        self.backup_dir = self.pasta / "backups"
        self.media_dir = self.pasta / "media"
        self.configuracao = override_settings(
            BACKUP_DIR=self.backup_dir,
            MEDIA_ROOT=self.media_dir,
        )
        self.configuracao.enable()
        self.addCleanup(self.configuracao.disable)

        self.ficheiro_media = self.media_dir / "pedidos" / "2026" / "anexo.pdf"
        self.ficheiro_media.parent.mkdir(parents=True, exist_ok=True)
        self.ficheiro_media.write_bytes(b"%PDF-1.4\nconteudo de teste\n")

    def test_comando_cria_zip_com_base_e_anexos(self):
        User.objects.create_user(
            username="aluno_backup",
            email="701222222@estudante.ucm.ac.mz",
            password="teste12345",
        )

        saida = StringIO()
        call_command("fazer_backup", stdout=saida)

        backups = sorted(self.backup_dir.glob("backup-*.zip"))
        self.assertEqual(len(backups), 1)
        caminho = backups[0]
        self.assertIn(caminho.name, saida.getvalue())
        self.assertIn("Backups guardados: 1", saida.getvalue())

        with zipfile.ZipFile(caminho) as arquivo:
            nomes = arquivo.namelist()
            self.assertIn("db.sqlite3", nomes)
            self.assertIn("media/pedidos/2026/anexo.pdf", nomes)
            extrair = self.pasta / "restauro"
            arquivo.extract("db.sqlite3", extrair)

        ligacao = sqlite3.connect(extrair / "db.sqlite3")
        try:
            total = ligacao.execute(
                "SELECT COUNT(*) FROM auth_user WHERE username = ?",
                ("aluno_backup",),
            ).fetchone()[0]
        finally:
            ligacao.close()
        self.assertEqual(total, 1)

    def test_opcao_manter_apaga_os_backups_mais_antigos(self):
        for _ in range(3):
            call_command("fazer_backup", stdout=StringIO())

        self.assertEqual(len(list(self.backup_dir.glob("backup-*.zip"))), 3)

        call_command("fazer_backup", manter=2, stdout=StringIO())
        self.assertEqual(len(list(self.backup_dir.glob("backup-*.zip"))), 2)

        call_command("fazer_backup", manter=1, stdout=StringIO())
        self.assertEqual(len(list(self.backup_dir.glob("backup-*.zip"))), 1)


class PaginacaoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tipo = TipoDocumento.objects.create(
            nome="Tipo paginação",
            taxa_licenciatura=Decimal("100"),
            taxa_mestrado=Decimal("100"),
            taxa_doutoramento=Decimal("100"),
        )
        cls.estudante = _utilizador(
            "aluno_paginacao",
            "701333333@estudante.ucm.ac.mz",
            Perfil.PAPEL_ESTUDANTE,
        )
        curso = Curso.objects.create(
            nome="Curso Paginação",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        perfil = cls.estudante.perfil
        perfil.curso = curso
        perfil.grau = curso.grau
        perfil.save(update_fields=["curso", "grau"])

        cls.secretaria = _utilizador(
            "secretaria_paginacao",
            "secretaria.paginacao@ucm.ac.mz",
            Perfil.PAPEL_SECRETARIA,
        )

    def _criar_pedidos(self, quantidade):
        for indice in range(quantidade):
            Pedido.objects.create(
                estudante=self.estudante,
                tipo=self.tipo,
                grau=self.estudante.perfil.grau,
                motivo=f"Pedido de paginação {indice}.",
            )

    def test_meus_pedidos_pagina_25_e_pagina_fora_do_limite(self):
        self._criar_pedidos(30)
        self.client.force_login(self.estudante)
        url = reverse("pedidos:meus_pedidos")

        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["page_obj"].paginator.per_page, 25)
        self.assertEqual(len(resposta.context["pedidos"]), 25)

        resposta = self.client.get(url, {"page": 2})
        self.assertEqual(len(resposta.context["pedidos"]), 5)

        resposta = self.client.get(url, {"page": 999})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["page_obj"].number, 2)
        self.assertEqual(len(resposta.context["pedidos"]), 5)

    def test_listas_vazias_nao_partem_a_paginacao(self):
        vazio = _utilizador(
            "aluno_sem_pedidos",
            "701444444@estudante.ucm.ac.mz",
            Perfil.PAPEL_ESTUDANTE,
        )
        curso = Curso.objects.create(
            nome="Curso Vazio",
            grau=Perfil.GRAU_LICENCIATURA,
        )
        perfil = vazio.perfil
        perfil.curso = curso
        perfil.grau = curso.grau
        perfil.save(update_fields=["curso", "grau"])

        self.client.force_login(vazio)
        resposta = self.client.get(reverse("pedidos:meus_pedidos"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.context["pedidos"]), 0)
        self.assertEqual(resposta.context["page_obj"].paginator.num_pages, 1)

        self.client.force_login(self.secretaria)
        resposta = self.client.get(reverse("pedidos:fila"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.context["pedidos"]), 0)
        self.assertEqual(resposta.context["page_obj"].paginator.num_pages, 1)

    def test_fila_do_pessoal_tambem_pagina_25(self):
        self._criar_pedidos(30)
        self.client.force_login(self.secretaria)
        url = reverse("pedidos:fila")

        resposta = self.client.get(url)
        self.assertEqual(len(resposta.context["pedidos"]), 25)

        resposta = self.client.get(url, {"page": 999})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context["page_obj"].number, 2)
        self.assertEqual(len(resposta.context["pedidos"]), 5)


@override_settings(
    DEBUG=False,
    ALLOWED_HOSTS=["testserver", "localhost"],
)
class PaginasErroTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.secretaria = _utilizador(
            "secretaria_erros",
            "secretaria.erros@ucm.ac.mz",
            Perfil.PAPEL_SECRETARIA,
        )
        cls.credito = _utilizador(
            "credito_erros",
            "credito.erros@ucm.ac.mz",
            Perfil.PAPEL_CREDITO,
        )
        cls.tipo = TipoDocumento.objects.create(
            nome="Tipo dos erros",
            taxa_licenciatura=Decimal("100"),
            taxa_mestrado=Decimal("100"),
            taxa_doutoramento=Decimal("100"),
        )
        cls.dono = _utilizador(
            "dono_pedido_erro",
            "701555555@estudante.ucm.ac.mz",
            Perfil.PAPEL_ESTUDANTE,
        )
        cls.dono.first_name = "NomePrivado"
        cls.dono.last_name = "ApelidoPrivado"
        cls.dono.save(update_fields=["first_name", "last_name"])
        cls.outro = _utilizador(
            "outro_pedido_erro",
            "701666666@estudante.ucm.ac.mz",
            Perfil.PAPEL_ESTUDANTE,
        )
        for estudante in (cls.dono, cls.outro):
            curso = Curso.objects.create(
                nome=f"Curso {estudante.username}",
                grau=Perfil.GRAU_LICENCIATURA,
            )
            perfil = estudante.perfil
            perfil.curso = curso
            perfil.grau = curso.grau
            perfil.save(update_fields=["curso", "grau"])

        cls.pedido = Pedido.objects.create(
            estudante=cls.dono,
            tipo=cls.tipo,
            grau=cls.dono.perfil.grau,
            motivo="Pedido privado do teste de 404.",
        )

    def test_pagina_403_usa_o_tema_e_devolve_o_codigo_certo(self):
        self.client.force_login(self.credito)
        resposta = self.client.get(reverse("painel"))

        self.assertEqual(resposta.status_code, 403)
        self.assertContains(resposta, "Acesso negado", status_code=403)
        self.assertContains(resposta, "empty-state", status_code=403)
        self.assertContains(
            resposta,
            f'href="{reverse("home")}"',
            status_code=403,
        )

    def test_pagina_404_usa_o_tema_e_devolve_o_codigo_certo(self):
        resposta = self.client.get("/esta-pagina-nao-existe/")

        self.assertEqual(resposta.status_code, 404)
        self.assertContains(
            resposta,
            "Página não encontrada",
            status_code=404,
        )
        self.assertContains(resposta, "empty-state", status_code=404)
        self.assertContains(
            resposta,
            f'href="{reverse("home")}"',
            status_code=404,
        )

    def test_404_nao_revela_um_recurso_sem_acesso(self):
        self.client.force_login(self.outro)
        resposta = self.client.get(
            reverse("pedidos:pedido_detalhe", args=[self.pedido.pk])
        )

        self.assertEqual(resposta.status_code, 404)
        conteudo = resposta.content.decode()
        self.assertNotIn(self.pedido.protocolo, conteudo)
        self.assertNotIn(self.dono.get_full_name(), conteudo)
        self.assertNotIn(self.dono.email, conteudo)
        self.assertContains(resposta, "Página não encontrada", status_code=404)
