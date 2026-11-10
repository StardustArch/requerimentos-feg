"""Testes unitários para a propriedade `Pedido.progresso`.

Cobre pedido com Registo (4 segmentos) e sem Registo (3 segmentos) em cada um
dos 4 estados, incluindo indeferido em cada etapa aplicável (incluindo
secretaria_final, que o código permite enquanto o estado é em_tratamento).
O histórico de datas vem de Decisao.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from contas.models import Curso, Perfil
from pedidos.models import Pedido, TipoDocumento, Decisao


class ProgressoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.curso = Curso.objects.create(
            nome="Licenciatura em Gestão", grau="licenciatura", activo=True
        )
        cls.user = User.objects.create_user(
            username="estudante_progresso",
            email="700000001@estudante.ucm.ac.mz",
            password="demo123",
        )
        # O signal cria o Perfil automaticamente; preenche-o aqui.
        cls.perfil = cls.user.perfil
        cls.perfil.papel = Perfil.PAPEL_ESTUDANTE
        cls.perfil.curso = cls.curso
        cls.perfil.grau = "licenciatura"
        cls.perfil.numero_estudante = "700000001"
        cls.perfil.save()

        cls.tipo_com_registo = TipoDocumento.objects.create(
            nome="Certificado normal",
            taxa_licenciatura=2500,
            taxa_mestrado=5000,
            taxa_doutoramento=10000,
            passa_registo_academico=True,
            prazo_estimado_dias=15,
            activo=True,
        )
        cls.tipo_sem_registo = TipoDocumento.objects.create(
            nome="Declaração simples",
            taxa_licenciatura=100,
            taxa_mestrado=200,
            taxa_doutoramento=300,
            passa_registo_academico=False,
            prazo_estimado_dias=None,
            activo=True,
        )

    def _criar_pedido(self, tipo, estado, etapa_actual, indeferido_na_etapa=""):
        return Pedido.objects.create(
            estudante=self.user,
            tipo=tipo,
            grau="licenciatura",
            motivo="Pedido de teste de progresso.",
            estado=estado,
            etapa_actual=etapa_actual,
            motivo_indeferimento="",
            indeferido_na_etapa=indeferido_na_etapa,
            valor_total=tipo.total("licenciatura"),
        )

    def _decisao(self, pedido, etapa, resultado):
        return Decisao.objects.create(
            pedido=pedido,
            etapa=etapa,
            resultado=resultado,
            justificacao="",
            decidido_por=self.user,
        )

    # ------------------------------------------------------------------
    # Helpers de afirmação
    # ------------------------------------------------------------------
    def _estados_segmentos(self, progresso):
        return [s["estado"] for s in progresso["segmentos"]]

    def _nomes_segmentos(self, progresso):
        return [s["nome"] for s in progresso["segmentos"]]

    # ------------------------------------------------------------------
    # Pedido COM registo (4 segmentos)
    # ------------------------------------------------------------------
    def test_com_registo_em_tratamento_no_credito(self):
        pedido = self._criar_pedido(
            self.tipo_com_registo,
            Pedido.ESTADO_EM_TRATAMENTO,
            Pedido.ETAPA_CREDITO,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 4)
        self.assertEqual(p["indice_actual"], 1)
        self.assertEqual(p["rotulo"], "etapa 2 de 4")
        self.assertEqual(
            self._nomes_segmentos(p),
            ["Secretaria", "Crédito", "Registo", "Assinatura"],
        )
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "actual", "pendente", "pendente"],
        )

    def test_com_registo_pronto(self):
        pedido = self._criar_pedido(
            self.tipo_com_registo,
            Pedido.ESTADO_PRONTO,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 4)
        self.assertEqual(p["indice_actual"], 3)
        self.assertEqual(p["rotulo"], "Pronto para levantamento")
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "concluida", "concluida", "concluida"],
        )

    def test_com_registo_entregue(self):
        pedido = self._criar_pedido(
            self.tipo_com_registo,
            Pedido.ESTADO_ENTREGUE,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 4)
        self.assertEqual(p["rotulo"], "Entregue")
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "concluida", "concluida", "concluida"],
        )

    def test_com_registo_indeferido_no_credito(self):
        pedido = self._criar_pedido(
            self.tipo_com_registo,
            Pedido.ESTADO_INDEFERIDO,
            Pedido.ETAPA_CREDITO,
            Pedido.ETAPA_CREDITO,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 4)
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "recusada", "pendente", "pendente"],
        )
        self.assertEqual(p["rotulo"], f"Indeferido em {Pedido.ETAPA_CREDITO}")

    def test_com_registo_indeferido_no_registo(self):
        pedido = self._criar_pedido(
            self.tipo_com_registo,
            Pedido.ESTADO_INDEFERIDO,
            Pedido.ETAPA_REGISTO,
            Pedido.ETAPA_REGISTO,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 4)
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "concluida", "recusada", "pendente"],
        )

    def test_com_registo_indeferido_em_secretaria_final(self):
        # O código permite indeferir em secretaria_final enquanto o estado
        # ainda é em_tratamento (indeferir nao exige etapa em ETAPAS_APROVACAO,
        # apenas que o pedido esteja em_tratamento).
        pedido = self._criar_pedido(
            self.tipo_com_registo,
            Pedido.ESTADO_INDEFERIDO,
            Pedido.ETAPA_SECRETARIA_FINAL,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 4)
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "concluida", "concluida", "recusada"],
        )

    def test_com_registo_historico_de_decisoes(self):
        pedido = self._criar_pedido(
            self.tipo_com_registo,
            Pedido.ESTADO_PRONTO,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )
        self._decisao(pedido, Pedido.ETAPA_SECRETARIA_RECEPCAO, Decisao.RESULTADO_APROVADO)
        self._decisao(pedido, Pedido.ETAPA_CREDITO, Decisao.RESULTADO_APROVADO)
        self._decisao(pedido, Pedido.ETAPA_REGISTO, Decisao.RESULTADO_APROVADO)
        self._decisao(
            pedido, Pedido.ETAPA_SECRETARIA_FINAL, Decisao.RESULTADO_PRONTO
        )
        pedido.refresh_from_db()
        p = pedido.progresso
        datas = [s["decisao"].data_hora for s in p["segmentos"]]
        self.assertTrue(all(d is not None for d in datas))
        self.assertEqual(len(datas), 4)

    # ------------------------------------------------------------------
    # Pedido SEM registo (3 segmentos)
    # ------------------------------------------------------------------
    def test_sem_registo_em_tratamento_na_recepcao(self):
        pedido = self._criar_pedido(
            self.tipo_sem_registo,
            Pedido.ESTADO_EM_TRATAMENTO,
            Pedido.ETAPA_SECRETARIA_RECEPCAO,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 3)
        self.assertEqual(p["indice_actual"], 0)
        self.assertEqual(p["rotulo"], "etapa 1 de 3")
        self.assertEqual(
            self._nomes_segmentos(p),
            ["Secretaria", "Crédito", "Assinatura"],
        )
        self.assertEqual(
            self._estados_segmentos(p),
            ["actual", "pendente", "pendente"],
        )

    def test_sem_registo_pronto(self):
        pedido = self._criar_pedido(
            self.tipo_sem_registo,
            Pedido.ESTADO_PRONTO,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 3)
        self.assertEqual(p["rotulo"], "Pronto para levantamento")
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "concluida", "concluida"],
        )

    def test_sem_registo_entregue(self):
        pedido = self._criar_pedido(
            self.tipo_sem_registo,
            Pedido.ESTADO_ENTREGUE,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 3)
        self.assertEqual(p["rotulo"], "Entregue")
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "concluida", "concluida"],
        )

    def test_sem_registo_indeferido_no_credito(self):
        pedido = self._criar_pedido(
            self.tipo_sem_registo,
            Pedido.ESTADO_INDEFERIDO,
            Pedido.ETAPA_CREDITO,
            Pedido.ETAPA_CREDITO,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 3)
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "recusada", "pendente"],
        )

    def test_sem_registo_indeferido_em_secretaria_final(self):
        pedido = self._criar_pedido(
            self.tipo_sem_registo,
            Pedido.ESTADO_INDEFERIDO,
            Pedido.ETAPA_SECRETARIA_FINAL,
            Pedido.ETAPA_SECRETARIA_FINAL,
        )
        p = pedido.progresso
        self.assertEqual(p["total"], 3)
        self.assertEqual(
            self._estados_segmentos(p),
            ["concluida", "concluida", "recusada"],
        )
