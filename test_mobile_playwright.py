#!/usr/bin/env python3
"""Teste Playwright para verificar bugs mobile (390px) e desktop (1440px)."""
import asyncio
import subprocess
import time
from pathlib import Path

from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
SCREENS_DIR = BASE_DIR / "docs" / "screens"
SCREENS_DIR.mkdir(parents=True, exist_ok=True)

SERVER_PROC = None


def iniciar_servidor():
    global SERVER_PROC
    SERVER_PROC = subprocess.Popen(
        [".venv/bin/python", "manage.py", "runserver", "127.0.0.1:8999"],
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    print("[servidor] Django iniciado na porta 8999")


def parar_servidor():
    global SERVER_PROC
    if SERVER_PROC:
        SERVER_PROC.terminate()
        try:
            SERVER_PROC.wait(timeout=5)
        except subprocess.TimeoutExpired:
            SERVER_PROC.kill()
        print("[servidor] Django parado")


async def testar_largura(largura, altura=800, nome="teste"):
    console_erros = []
    page_erros = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": largura, "height": altura},
        )
        page = await context.new_page()

        # Capturar TODOS os erros de console
        page.on("console", lambda msg: console_erros.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: page_erros.append(str(exc)))

        url = "http://127.0.0.1:8999/pedidos/staff/fila/"
        print(f"\n[{nome}] Acedendo a {url} em {largura}x{altura}")
        await page.goto(url, wait_until="networkidle")

        # Login como credito1
        print(f"[{nome}] Fazendo login...")
        await page.fill('input[name="username"]', "credito1")
        await page.fill('input[name="password"]', "demo123")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000)

        # Verificar se estamos logados (redirecionado para home ou fila)
        url_atual = page.url
        print(f"[{nome}] URL após login: {url_atual}")

        # Tirar screenshot inicial
        await page.screenshot(path=SCREENS_DIR / f"{nome}_inicial.png")
        print(f"[{nome}] Screenshot inicial guardado")

        # Verificar se o botão hambúrguer existe
        toggle = page.locator("[data-sidebar-toggle]")
        toggle_count = await toggle.count()
        print(f"[{nome}] Botão hambúrguer encontrado: {toggle_count} vez(es)")

        if largura <= 640:
            # Mobile: verificar sidebar fechada por defeito
            sidebar = page.locator("[data-sidebar]")
            sidebar_box = await sidebar.bounding_box()
            print(f"[{nome}] Sidebar left inicial: {sidebar_box['x']}px (deve ser negativo = fechada)")

            # Clicar no hambúrguer
            print(f"[{nome}] Clicando no botão hambúrguer...")
            await toggle.click()
            await page.wait_for_timeout(1500)

            # Verificar se a sidebar abriu
            sidebar_box = await sidebar.bounding_box()
            print(f"[{nome}] Sidebar left após clique: {sidebar_box['x']}px")

            # Screenshot
            await page.screenshot(path=SCREENS_DIR / f"{nome}_apos_clique.png")
            print(f"[{nome}] Screenshot após clique guardado")

            # Verificar classes da sidebar
            classes = await sidebar.get_attribute("class")
            print(f"[{nome}] Classes da sidebar: {classes}")

            # Verificar atributo aria-expanded
            aria = await toggle.get_attribute("aria-expanded")
            print(f"[{nome}] aria-expanded do botão: {aria}")

        else:
            # Desktop: sidebar sempre visível
            sidebar = page.locator("[data-sidebar]")
            sidebar_box = await sidebar.bounding_box()
            print(f"[{nome}] Sidebar left em desktop: {sidebar_box['x']}px")

        # Verificar scrollWidth
        scroll_width = await page.evaluate("document.documentElement.scrollWidth")
        client_width = await page.evaluate("document.documentElement.clientWidth")
        print(f"[{nome}] scrollWidth={scroll_width}, clientWidth={client_width}")

        # Verificar tabelas
        tabelas = page.locator(".data-table")
        count = await tabelas.count()
        print(f"[{nome}] Tabelas encontradas: {count}")
        for i in range(count):
            tabela = tabelas.nth(i)
            diff = await tabela.evaluate("(el) => el.scrollWidth - el.clientWidth")
            print(f"[{nome}] Tabela {i}: scrollWidth-clientWidth={diff}")

        # Screenshot completo
        await page.screenshot(path=SCREENS_DIR / f"{nome}_completa.png", full_page=True)

        # Reportar erros
        if console_erros:
            print(f"[{nome}] ERROS DE CONSOLE ({len(console_erros)}):")
            for e in console_erros:
                print(f"  - {e}")
        else:
            print(f"[{nome}] Nenhum erro de console")

        if page_erros:
            print(f"[{nome}] ERROS DE PÁGINA ({len(page_erros)}):")
            for e in page_erros:
                print(f"  - {e}")
        else:
            print(f"[{nome}] Nenhum erro de página")

        await browser.close()

    return console_erros, page_erros


async def main():
    iniciar_servidor()
    try:
        await testar_largura(390, 800, "mobile_390")
        await testar_largura(1440, 900, "desktop_1440")
    finally:
        parar_servidor()


if __name__ == "__main__":
    asyncio.run(main())
