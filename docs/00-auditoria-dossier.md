# 00. Auditoria do dossier (antes da actualização)

Comparação de cada ficheiro `docs/00` a `docs/14` com o código actual
(pós-migração Bootstrap/HTMX → Tailwind/Unpoly). Cada linha tem uma etiqueta:

- `OK sem alterações` — continua correcto tal como está.
- `ACTUALIZAR` — contém factos desactualizados que devem ser corrigidos.
- `REVER` — contém factos possivelmente desactualizados; verificar se há
  discrepância real antes de editar.

Evidência = o que no código contradiz o texto actual.

| Ficheiro | Etiqueta | Motivo / evidência |
|----------|----------|--------------------|
| `00-varredura.md` | ACTUALIZAR | Inventário ainda cita Bootstrap, HTMX, Chart.js, `static/vendor/`, `ucm-theme.css`, `django_tailwind_cli` em falta, número de testes desactualizado, estrutura de pastas desatualizada (sem `templates/components`, sem `static/css/app.css`/`input.css`, sem `static/fonts`, sem `static/vendor/unpoly`). |
| `01-visao-geral.md` | ACTUALIZAR | Stack cita Bootstrap 5 + HTMX + Chart.js (secção 1.4); instalação não menciona build do Tailwind; estrutura de pastas desatualizada. |
| `02-requisitos.md` | ACTUALIZAR | RF06 cita HTMX (`pedidos.views.resumo_pedido` via HTMX); RNF04 cita tema Bootstrap/topbar/navbar; não há RNF de "offline sem CDN" nem de responsividade mobile com evidência nova. |
| `03-casos-de-uso.md` | OK sem alterações | Casos de uso, actores e fluxos são de negócio; não referem HTMX nem Bootstrap. Não há alteração de rotas nem de permissões. |
| `04-diagramas-actividade-sequencia.md` | REVER | A secção 4.2 (submissão) menciona explicitamente "resumo da taxa buscado via HTMX" e o participante `HTMX` no diagrama de sequência. O resto (regras de negócio, decisões, backup) está correcto. |
| `05-modelo-de-dados.md` | OK sem alterações | Modelos, ER, dicionário de dados e fluxo de estados não mudaram com a migração do frontend. |
| `06-regras-de-negocio.md` | OK sem alterações | Regras de negócio, transições, permissões, validações, taxas e auditoria são de backend; inalterados. |
| `07-arquitectura.md` | ACTUALIZAR | Camada de apresentação cita "views, HTMX"; diagrama de componentes cita "Static - Bootstrap, HTMX, Chart.js"; secção 7.6 lista Bootstrap 5, Bootstrap Icons, HTMX — tudo desactualizado. Falta Unpoly, Tailwind, pipeline CSS (input.css → app.css), fonte Inter, ícones Lucide. |
| `08-permissoes.md` | OK sem alterações | Tabela de permissões por view/rota e decoradores não mudaram com a migração do frontend. |
| `09-interface.md` | ACTUALIZAR | Componentes UI citam Bootstrap 5, `ucm-theme.css`, Bootstrap Icons, HTMX, classes Bootstrap `col-*`/`container`/`navbar-expand-lg`; tela "Resumo da taxa (HTMX)" (linha 21); não há menção a sidebar, topbar, componentes em `templates/components`, tokens de design, nem responsividade mobile com drawer. |
| `10-testes.md` | ACTUALIZAR | Resultado cita 96 testes (deve ser re-executado para confirmar o número real); matriz RF06 cita "Endpoint HTMX"; nome de teste legado `test_endpoint_htmx_devolve_a_taxa_certa_para_cada_grau` existe em `pedidos/tests.py`. |
| `11-evidencias.md` | REVER | Checklist cita tela 10 "Resumo da taxa (HTMX)"; `docs/screens/` tem 5 PNG (desktop/mobile); verificar se faltam capturas das telas novas (sidebar, topbar). |
| `12-limitacoes-e-trabalho-futuro.md` | REVER | Não menciona dependência do build do Tailwind nem uso limitado de Unpoly; deve acrescentar. |
| `13-mapa-para-a-monografia.md` | REVER | Não lista `14-glossario` como fonte de novos termos (Unpoly, Tailwind, sidebar); pode precisar de acréscimo. |
| `14-glossario-e-abreviaturas.md` | ACTUALIZAR | Abreviaturas 29-31 citam HTMX, Chart.js, Bootstrap como se estivessem activos; falta Unpoly, Tailwind CSS, sidebar, drawer, ícones Lucide, fonte Inter. |

## Resumo da auditoria

- **ACTUALIZAR (9):** 00, 01, 02, 07, 09, 10, 11 (rever), 12 (rever), 13 (rever), 14
- **REVER (4):** 04, 11, 12, 13
- **OK sem alterações (5):** 03, 05, 06, 08

### Factos confirmados no código actual (base para as actualizações)

- Frontend: Tailwind CSS v4 (`static/css/app.css` compilado de `static/css/input.css` via `tailwind.config.js`), fonte Inter local (`static/fonts/*.woff2`), ícones Lucide SVG (`templates/components/icon.html`), Unpoly (`static/vendor/unpoly/unpoly.min.js/.css`).
- Sem CDN; sem referências a `hx-*`, `htmx`, Bootstrap em templates nem Python (só o nome de um teste legado).
- `django-tailwind-cli` v4.8.2 em `requirements.txt`? Não — não está no `requirements.txt` (verificado). Está em `INSTALLED_APPS` e settings têm `TAILWIND_*`.
- `templates/components/` existe com `icon.html`, `table_wrap.html`, `table_wrap_open.html`, `table_wrap_close.html`.
- `base.html`: sidebar fixa (drawer mobile com `data-sidebar-toggle`/overlay), topbar `h-14`, toasts, meta CSRF para Unpoly, `up-target="#resumo-pedido"` + `up-autosubmit` no `novo_pedido.html`.
- `novo_pedido.html`: select de tipo com `up-target="#resumo-pedido"` `up-autosubmit` (Unpoly, substitui HTMX); `_resumo_pedido.html` com `id="resumo-pedido"`.
- Painel (`painel.html`) mantém Chart.js (não alvo da migração).
- Bootstrap ficheiros físicos permanecem em `static/vendor/bootstrap/` mas não são referenciados.
- Não existe cache-buster em `base.html` nem em `app.css` (verificado).
- Testes: `python manage.py test` → **Ran 96 tests, OK** (confirmado em execução real).
- `docs/screens/` tem 5 PNG: `desktop_1440_completa.png`, `desktop_1440_inicial.png`, `mobile_390_apos_clique.png`, `mobile_390_completa.png`, `mobile_390_inicial.png`.
- Fases de migração (git log): Fase 1 (2126283: Bootstrap/HTMX → Tailwind), Fase 2 (ee81d56: HTMX → Unpoly), Fase 3 (10b04c6: README + resumo da migração), correção mobile (438d4de), remoção executável Tailwind (94b8cfb).
- Migração sustentada por `docs/migracao-resumo.md` e `docs/migracao-00-inventario.md`.

### "NÃO EXISTE" / "(deduzido)" novos identificados nesta auditoria

- `django-tailwind-cli` **não está em `requirements.txt`** (está em `INSTALLED_APPS` e settings) — deduzido de `requirements.txt` + `config/settings.py`.
- Não existe cache-buster (cache buster) em `base.html` nem `static/css/app.css` — deduzido por busca no código.
- Não existe pasta `scripts/` — existe apenas `tools/check_classes.py` — deduzido de `ls tools/ scripts/`.
- Número real de testes: **96** (confirmado com `python manage.py test`), não deduzido.

Parei aqui e apresento a tabela. Aguardo confirmação para prosseguir ao PASSO 2 (actualização dos ficheiros marcados).
