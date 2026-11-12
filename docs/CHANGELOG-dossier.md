# Changelog do dossier técnico

Registo das alterações feitas ao dossier `docs/` para reflectir a migração do
frontend (Bootstrap/HTMX → Tailwind CSS v4 + Unpoly). Os ficheiros `docs/migracao-*.md`
e `docs/screens/` não foram alterados nem apagados.

## Novos ficheiros

| Ficheiro | Alteração |
|----------|-----------|
| `docs/00-auditoria-dossier.md` | Criado: tabela de auditoria de docs/00 a 14 com etiqueta, motivo e evidência. |
| `docs/15-evolucao-do-projecto.md` | Criado: cronologia a partir do `git log` (fases A, B, C) e porquê da migração. |
| `docs/CHANGELOG-dossier.md` | Criado: este registo. |

## Ficheiros actualizados

| Ficheiro | Alteração (1-3 linhas) |
|----------|------------------------|
| `docs/00-varredura.md` | Dependências (nota sobre `django-tailwind-cli` não em `requirements.txt`); estrutura de pastas (componentes, CSS app.css/input.css, fontes, vendor/unpoly, tailwind sem rastrear executável); resumo_pedido sem HTMX; ficheiros estáticos reescritos (sem HTMX/Bootstrap referenciados); fluxo de submissão com Unpoly. |
| `docs/01-visao-geral.md` | Stack: Tailwind v4 + Unpoly + Lucide + fonte Inter (sem Bootstrap/HTMX); instalação acrescenta passo `python manage.py tailwind build`. |
| `docs/02-requisitos.md` | RF06 sem menção a HTMX; RNF04 tema Tailwind; novos RNF11 (offline sem CDN) e RNF12 (responsividade mobile: drawer + tabelas com scroll). |
| `docs/04-diagramas-actividade-sequencia.md` | Secção 4.2: resumo da taxa via Unpoly (não HTMX); participante do diagrama de sequência renomeado para Unpoly. |
| `docs/07-arquitectura.md` | Camada de apresentação sem HTMX; fluxo ponta-a-ponta com Unpoly; diagrama de componentes com Tailwind/Unpoly/fonts; secção 7.6 reescrita (Tailwind, Unpoly, Lucide, Inter, sem CDN). |
| `docs/09-interface.md` | Componentes UI reescritos (sidebar, topbar, `templates/components`, tokens de design, Unpoly, table_wrap); secção 9.2 tokens por estado; secção 9.5 capturas de ecrã existentes e em falta em `docs/screens/`. |
| `docs/10-testes.md` | Resultado real confirmado (96 testes, 0 falhas); teste legado com nome "htmx" identificado e explicado; matriz RF06 ajustada. |
| `docs/11-evidencias.md` | Tela 10 sem HTMX (Unpoly); nova secção 11.3 com estado de `docs/screens/` (5 PNG existentes, lista de faltantes). |
| `docs/12-limitacoes-e-trabalho-futuro.md` | Novas limitações: dependência do build do Tailwind, uso limitado de Unpoly (só select de tipo), ausência de cache-buster no CSS. |
| `docs/14-glossario-e-abreviaturas.md` | HTMX marcado como removido; acrescidos Unpoly, Tailwind CSS, Lucide, Inter, sidebar, drawer, token de design, progressive enhancement; Bootstrap ajustado (não referenciado). |

## Ficheiros actualizados (documentação da barra de progresso — commit 49a70a5)

| Ficheiro | Alteração (1-3 linhas) |
|----------|------------------------|
| `docs/02-requisitos.md` | Novo RF32: estudante vê barra de progresso na lista "Meus pedidos" (3 ou 4 segmentos consoante `passa_registo_academico`). |
| `docs/03-casos-de-uso.md` | CU05: lista "Meus pedidos" e detalhe mostram a barra de progresso (variantes compact/full). |
| `docs/06-regras-de-negocio.md` | Nova secção 6.4: regra de negócio da barra de progresso (etapas aplicáveis, estados, rótulos). |
| `docs/09-interface.md` | Componente `progress_steps.html` na tabela UI; tela "Meus pedidos" com barra de progresso. |
| `docs/10-testes.md` | Total de testes passa de 96 para 108; novo ficheiro `test_progresso.py` (12 testes); matriz RF32. |
| `docs/15-evolucao-do-projecto.md` | Commit `49a70a5` na fase C; contagem de testes actualizada para 108/108. |

## Ficheiros sem alterações

| Ficheiro | Motivo |
|----------|--------|
| `docs/05-modelo-de-dados.md` | Modelos e fluxo de estados inalterados (a propriedade `progresso` não altera o modelo de dados). |
| `docs/08-permissoes.md` | Tabela de permissões e decoradores inalterados. |
| `docs/13-mapa-para-a-monografia.md` | Mapeamento de ficheiros para secções da monografia ainda válido. |
| `docs/migracao-*.md` | Não alterados (regra de preservação). |
| `docs/screens/` | Não apagados nem alterados (capturas existentes mantidas; novas capturas da barra de progresso não foram solicitadas nesta tarefa). |
