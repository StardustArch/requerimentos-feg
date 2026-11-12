#!/usr/bin/env python3
"""Auditoria de UI por estilos computados (Playwright).

Verifica, nas telas do estudante e do staff em 1440px:
  a) <a>, <button>, input[type=submit] com classe btn* ou fundo não-transparente
     com padding horizontal == 0 ou altura < 36px;
  b) <a> dentro de <main> que funcionam como acção mas não têm classe de botão;
  c) textarea, select e input sem borda visível;
  d) input[type=file] sem estilo.

Uso:
  .venv/bin/python tools/audit_ui.py
Requer o servidor a correr em http://127.0.0.1:8997 (iniciar manualmente com
`python manage.py runserver 127.0.0.1:8997`) ou defina UI_BASE_URL.
"""

import asyncio
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

BASE_URL = os.environ.get("UI_BASE_URL", "http://127.0.0.1:8997")
WIDTH, HEIGHT = 1440, 900

SCREENS = [
    ("/", "Estudante — Início", "estudante1"),
    ("/pedidos/novo/", "Estudante — Novo pedido", "estudante1"),
    ("/pedidos/meus/", "Estudante — Meus pedidos", "estudante1"),
    ("/pedidos/staff/fila/", "Staff — Fila", "secretaria1"),
    ("/pedidos/staff/pesquisa/", "Staff — Pesquisa", "secretaria1"),
]

DETAIL_SCREENS = [
    ("/pedidos/1/", "Estudante/Staff — Detalhe do pedido (pk=1)", "estudante1"),
]

BUTTON_CLASSES = ("btn", "btn-primary", "btn-secondary", "btn-outline",
                  "btn-ghost", "btn-danger")


async def _pl(el):
    return await el.evaluate("(el) => parseInt(getComputedStyle(el).paddingLeft) || 0")


async def _pr(el):
    return await el.evaluate("(el) => parseInt(getComputedStyle(el).paddingRight) || 0")


async def _bg(el):
    return await el.evaluate("(el) => getComputedStyle(el).backgroundColor")


async def _bw(el):
    return await el.evaluate("(el) => parseInt(getComputedStyle(el).borderWidth) || 0")


async def _text(el):
    return (await el.inner_text())[:60]


async def _tag(el):
    return await el.evaluate("(el) => el.tagName.toLowerCase()")


async def _cls(el):
    return await el.get_attribute("class") or ""


async def main():
    results = {"a": [], "b": [], "c": [], "d": []}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
        )
        page = await context.new_page()
        console_erros = []
        page.on("console", lambda msg: console_erros.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: console_erros.append(str(exc)))

        for path, desc, user in SCREENS:
            await _audit_url(page, path, desc, user, results)

        for path, desc, user in DETAIL_SCREENS:
            await _audit_url(page, path, desc, user, results)

        await browser.close()

    _imprimir_resultados(results)
    if console_erros:
        print("\nERROS DE CONSOLE durante a auditoria:")
        for e in console_erros:
            print(f"  - {e}")

    total = sum(len(v) for v in results.values())
    sys.exit(1 if total > 0 else 0)


async def _audit_url(page, path, desc, user, results):
    url = f"{BASE_URL}{path}"
    print(f"\n===== {desc} ({url}) =====")
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(800)

    login_form = await page.locator('form input[name="username"]').count()
    if login_form:
        await page.fill('input[name="username"]', user)
        await page.fill('input[name="password"]', "demo123")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(1000)
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(800)

    # a) Botões/links de acção com padding horizontal 0 ou altura < 36px
    candidates = await page.locator("a, button, input[type=submit]").all()
    for el in candidates:
        cls = await _cls(el)
        if not any(c in cls.split() for c in BUTTON_CLASSES):
            continue
        box = await el.bounding_box()
        if not box:
            continue
        pl = await _pl(el)
        pr = await _pr(el)
        bg = await _bg(el)
        has_bg = bg not in ("transparent", "rgba(0, 0, 0, 0)")
        if (pl == 0 and pr == 0) or box["height"] < 36 or (has_bg and box["height"] < 36):
            tag = await _tag(el)
            text = await _text(el)
            results["a"].append(
                f"{tag}:? — {desc} — cls='{cls}' h={box['height']:.0f}px "
                f"px={pl}/{pr} bg={bg} texto='{text}'"
            )

    # b) <a> dentro de <main> que parecem acção mas não têm classe de botão
    links = await page.locator("main a").all()
    for el in links:
        href = await el.get_attribute("href")
        cls = await _cls(el)
        if not href or href.startswith("#"):
            continue
        if any(c in cls.split() for c in BUTTON_CLASSES):
            continue
        text = (await el.inner_text()).strip()
        if not text or len(text) > 60:
            continue
        tag = await _tag(el)
        results["b"].append(
            f"{tag}:? — {desc} — href='{href}' cls='{cls}' texto='{text}'"
        )

    # c) textarea, select, input sem borda visível
    inputs = await page.locator("textarea, select, input").all()
    for el in inputs:
        type_attr = await el.get_attribute("type") or "text"
        if type_attr in ("hidden", "submit", "button", "file", "checkbox", "radio"):
            continue
        tag = await _tag(el)
        cls = await _cls(el)
        bw = await _bw(el)
        if bw == 0:
            results["c"].append(
                f"{tag}:? — {desc} — type='{type_attr}' cls='{cls}' "
                f"borderWidth={bw}"
            )

    # d) input[type=file] sem estilo
    files = await page.locator("input[type=file]").all()
    for el in files:
        cls = await _cls(el)
        box = await el.bounding_box()
        styled = bool(cls.strip()) or (box and box["width"] > 0)
        if not styled:
            results["d"].append(
                f"input[type=file]:? — {desc} — cls='{cls}'"
            )


def _imprimir_resultados(results):
    categorias = {
        "a": "a) Botões com padding horizontal == 0 ou altura < 36px",
        "b": "b) <a> acção dentro de <main> sem classe de botão",
        "c": "c) textarea/select/input sem borda visível",
        "d": "d) input[type=file] sem estilo",
    }
    total = 0
    for key, titulo in categorias.items():
        itens = results[key]
        total += len(itens)
        print(f"\n{titulo}: {len(itens)}")
        for item in itens:
            print(f"  - {item}")
    print(f"\nTOTAL: {total} problemas")


if __name__ == "__main__":
    asyncio.run(main())
