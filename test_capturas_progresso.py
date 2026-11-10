#!/usr/bin/env python3
"""Capturas da lista do estudante (/pedidos/meus/) em 1440px e 390px.

Gera uma captura por largura com um pedido de cada estado visível
(em tratamento, pronto, entregue, indeferido), carregado via seed_demo.
Guardado em docs/screens/.
"""
import asyncio
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
SCREENS_DIR = BASE_DIR / "docs" / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)

SERVER_PROC = None


def run(cmd):
    return subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True)


def preparar_ambiente():
    run([".venv/bin/python", "manage.py", "migrate", "--run-syncdb"])
    run([".venv/bin/python", "manage.py", "seed_demo"])


def iniciar_servidor():
    global SERVER_PROC
    SERVER_PROC = subprocess.Popen(
        [".venv/bin/python", "manage.py", "runserver", "127.0.0.1:8998"],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    print("[servidor] Django iniciado na porta 8998")


def parar_servidor():
    global SERVER_PROC
    if SERVER_PROC:
        SERVER_PROC.terminate()
        try:
            SERVER_PROC.wait(timeout=5)
        except subprocess.TimeoutExpired:
            SERVER_PROC.kill()
        print("[servidor] Django parado")


async def capturar(largura, altura, nome):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": largura, "height": altura})
        page = await context.new_page()
        console_erros = []
        page.on("console", lambda msg: console_erros.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console_erros.append(str(exc)))

        print(f"\n[{nome}] Acedendo a /pedidos/meus/ em {largura}x{altura}")
        await page.goto("http://127.0.0.1:8998/pedidos/meus/", wait_until="networkidle")

        # Login como estudante1
        await page.fill('input[name="username"]', "estudante1")
        await page.fill('input[name="password"]', "demo123")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)

        # Esperar a lista carregar
        await page.wait_for_selector("table.data-table", timeout=10000)
        await page.wait_for_timeout(1000)

        # Verificar sem scroll horizontal
        scroll_width = await page.evaluate("document.documentElement.scrollWidth")
        client_width = await page.evaluate("document.documentElement.clientWidth")
        print(f"[{nome}] scrollWidth={scroll_width}, clientWidth={client_width}")

        await page.screenshot(path=SCREENS_DIR / f"{nome}.png", full_page=True)
        print(f"[{nome}] Captura guardada: {nome}.png")

        if console_erros:
            print(f"[{nome}] ERROS DE CONSOLE ({len(console_erros)}):")
            for e in console_erros:
                print(f"  - {e}")
        else:
            print(f"[{nome}] Nenhum erro de console")

        await browser.close()


async def main():
    preparar_ambiente()
    iniciar_servidor()
    try:
        await capturar(1440, 900, "lista_estudante_1440")
        await capturar(390, 900, "lista_estudante_390")
    finally:
        parar_servidor()


if __name__ == "__main__":
    asyncio.run(main())
