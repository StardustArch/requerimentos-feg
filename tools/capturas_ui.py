#!/usr/bin/env python3
"""Capturas de ecrã da UI corrigida em 1440px e 390px.

Gera pedidos de teste nos estados necessários, inicia o servidor Django e
tira capturas de:
  - Login
  - Estudante: Início, Novo pedido (vazio e com erros), Meus pedidos,
    Detalhe (pronto, em tratamento, indeferido)
  - Staff: Início, Fila, Pesquisa, Detalhe
  - Styleguide

Guardado em docs/screens/.
"""
import asyncio
import os
import sys
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ["DJANGO_DEBUG"] = "True"  # styleguide só acessível com DEBUG=True
import django  # noqa: E402

django.setup()  # noqa: E402

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from contas.models import Curso, Perfil  # noqa: E402
from pedidos.models import Pedido, TipoDocumento  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402

from playwright.async_api import async_playwright  # noqa: E402

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
SCREENS_DIR = BASE_DIR / "docs" / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)
BASE_URL = "http://127.0.0.1:8996"

SERVER_PROC = None


def preparar_dados():
    """Garante um utilizador e pedidos nos estados necessários na BD principal."""
    curso, _ = Curso.objects.get_or_create(
        nome="Licenciatura em Gestão", grau="licenciatura", defaults={"activo": True}
    )
    tipo, _ = TipoDocumento.objects.get_or_create(
        nome="Certificado normal",
        defaults={
            "taxa_licenciatura": 2500,
            "taxa_mestrado": 5000,
            "taxa_doutoramento": 10000,
            "passa_registo_academico": True,
            "prazo_estimado_dias": 15,
            "activo": True,
        },
    )

    user, _ = User.objects.get_or_create(
        username="captura_estudante",
        defaults={"email": "700000002@estudante.ucm.ac.mz"},
    )
    perfil = user.perfil
    perfil.papel = Perfil.PAPEL_ESTUDANTE
    perfil.curso = curso
    perfil.grau = "licenciatura"
    perfil.numero_estudante = "700000002"
    perfil.save()
    user.set_password("demo123")
    user.save()

    def criar(estado, etapa):
        return Pedido.objects.create(
            estudante=user,
            tipo=tipo,
            grau="licenciatura",
            motivo="Pedido de captura de ecrã da UI.",
            estado=estado,
            etapa_actual=etapa,
            valor_total=tipo.total("licenciatura"),
        )

    existentes = {
        (p.estado, p.etapa_actual) for p in Pedido.objects.filter(estudante=user)
    }
    alvos = [
        (Pedido.ESTADO_EM_TRATAMENTO, Pedido.ETAPA_CREDITO),
        (Pedido.ESTADO_PRONTO, Pedido.ETAPA_SECRETARIA_FINAL),
        (Pedido.ESTADO_INDEFERIDO, Pedido.ETAPA_CREDITO),
    ]
    pedidos = {}
    for estado, etapa in alvos:
        if (estado, etapa) not in existentes:
            pedidos[(estado, etapa)] = criar(estado, etapa)
        else:
            pedidos[(estado, etapa)] = Pedido.objects.filter(
                estudante=user, estado=estado, etapa_actual=etapa
            ).first()

    return user, pedidos


def iniciar_servidor():
    global SERVER_PROC
    env = os.environ.copy()
    env["DJANGO_DEBUG"] = "True"
    SERVER_PROC = subprocess.Popen(
        [".venv/bin/python", "manage.py", "runserver", "127.0.0.1:8996"],
        cwd=BASE_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    print("[servidor] Django iniciado na porta 8996")


def parar_servidor():
    global SERVER_PROC
    if SERVER_PROC:
        SERVER_PROC.terminate()
        try:
            SERVER_PROC.wait(timeout=5)
        except subprocess.TimeoutExpired:
            SERVER_PROC.kill()
        print("[servidor] Django parado")


async def fazer_login(page, username="captura_estudante", senha="demo123"):
    await page.fill('input[name="username"]', username)
    await page.fill('input[name="password"]', senha)
    await page.click('button[type="submit"]')
    await page.wait_for_timeout(1000)


async def capturar(page, largura, altura, nome, url, usuario=None):
    print(f"\n[{nome}] {url} em {largura}x{altura}")
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(800)

    login_form = await page.locator('form input[name="username"]').count()
    if login_form and usuario:
        await fazer_login(page, usuario.username)
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(800)

    # Novo pedido com erros: submeter vazio para gerar erros de validação
    if "com-erros" in nome:
        btn = page.locator('button[type="submit"]')
        if await btn.count():
            await btn.click()
            await page.wait_for_timeout(1000)

    await page.screenshot(path=SCREENS_DIR / f"{nome}.png", full_page=True)
    print(f"[{nome}] guardado: {nome}.png")


async def main(usuario, pedidos):
    p_trat = pedidos[
        (Pedido.ESTADO_EM_TRATAMENTO, Pedido.ETAPA_CREDITO)
    ]
    p_pronto = pedidos[(Pedido.ESTADO_PRONTO, Pedido.ETAPA_SECRETARIA_FINAL)]
    p_indef = pedidos[(Pedido.ESTADO_INDEFERIDO, Pedido.ETAPA_CREDITO)]

    iniciar_servidor()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for largura, altura in [(1440, 900), (390, 900)]:
                sufixo = "1440" if largura == 1440 else "390"
                context = await browser.new_context(
                    viewport={"width": largura, "height": altura}
                )
                page = await context.new_page()

                await capturar(
                    page, largura, altura, f"login_{sufixo}",
                    f"{BASE_URL}/contas/login/", usuario,
                )
                await capturar(
                    page, largura, altura, f"estudante_inicio_{sufixo}",
                    f"{BASE_URL}/", usuario,
                )
                await capturar(
                    page, largura, altura,
                    f"estudante_novopedido_vazio_{sufixo}",
                    f"{BASE_URL}/pedidos/novo/", usuario,
                )
                await capturar(
                    page, largura, altura,
                    f"estudante_novopedido_com_erros_{sufixo}",
                    f"{BASE_URL}/pedidos/novo/", usuario,
                )
                await capturar(
                    page, largura, altura, f"estudante_meuspedidos_{sufixo}",
                    f"{BASE_URL}/pedidos/meus/", usuario,
                )
                await capturar(
                    page, largura, altura,
                    f"estudante_detalhe_tratamento_{sufixo}",
                    f"{BASE_URL}/pedidos/{p_trat.pk}/", usuario,
                )
                await capturar(
                    page, largura, altura,
                    f"estudante_detalhe_pronto_{sufixo}",
                    f"{BASE_URL}/pedidos/{p_pronto.pk}/", usuario,
                )
                await capturar(
                    page, largura, altura,
                    f"estudante_detalhe_indeferido_{sufixo}",
                    f"{BASE_URL}/pedidos/{p_indef.pk}/", usuario,
                )
                await capturar(
                    page, largura, altura, f"staff_inicio_{sufixo}",
                    f"{BASE_URL}/", "secretaria1",
                )
                await capturar(
                    page, largura, altura, f"staff_fila_{sufixo}",
                    f"{BASE_URL}/pedidos/staff/fila/", "secretaria1",
                )
                await capturar(
                    page, largura, altura, f"staff_pesquisa_{sufixo}",
                    f"{BASE_URL}/pedidos/staff/pesquisa/", "secretaria1",
                )
                await capturar(
                    page, largura, altura, f"staff_detalhe_{sufixo}",
                    f"{BASE_URL}/pedidos/staff/{p_trat.pk}/", "secretaria1",
                )
                await capturar(
                    page, largura, altura, f"styleguide_{sufixo}",
                    f"{BASE_URL}/dev/styleguide/",
                )

                await context.close()
            await browser.close()
    finally:
        parar_servidor()


if __name__ == "__main__":
    usuario, pedidos = preparar_dados()
    asyncio.run(main(usuario, pedidos))
