# 11. Evidências — capturas de ecrã e roteiro de vídeo

## 11.1 Checklist de capturas de ecrã

Uma captura por tela e por perfil, utilizando os utilizadores de demonstração
criados por `python manage.py seed_demo` (`pedidos/management/commands/seed_demo.py`):
`admin`, `secretaria1`, `credito1`, `registo1`, `estudante1` (palavra-passe
`demo123`, ou o valor de `DEMO_PASSWORD`).

| # | Tela | URL | Utilizador demo | O que deve aparecer |
| --- | --- | --- | --- | --- |
| 1 | Login | `/contas/login/` | — (não autenticado) | Formulário username/password + botão Google (se configurado) |
| 2 | Página inicial (estudante) | `/` | `estudante1` | Área do estudante: Novo pedido, Meus pedidos, Dados académicos |
| 3 | Página inicial (secretaria) | `/` | `secretaria1` | Área da Secretaria: contagens da fila + Painel |
| 4 | Página inicial (crédito) | `/` | `credito1` | Área de Controlo de Crédito: contagem da fila |
| 5 | Página inicial (registo) | `/` | `registo1` | Área de Registo Académico: contagem da fila |
| 6 | Página inicial (admin) | `/` | `admin` | Área de Administração: todas as contagens + Gestão |
| 7 | Completar perfil | `/contas/completar-perfil/` | `estudante1` | Escolha de curso por grau |
| 8 | Bloqueio de número | (redireccionado) | estudante sem número | Mensagem: não foi possível identificar o número |
| 9 | Novo pedido | `/pedidos/novo/` | `estudante1` | Formulário tipo/motivo/anexos + resumo da taxa |
| 10 | Resumo da taxa (HTMX) | `/pedidos/resumo/?tipo=X` | `estudante1` | Taxa base, IVA, total, prazo |
| 11 | Meus pedidos | `/pedidos/meus/` | `estudante1` | Lista paginada de pedidos |
| 12 | Detalhe do pedido | `/pedidos/<pk>/` | `estudante1` | Detalhe + anexos visíveis |
| 13 | Fila (secretaria) | `/pedidos/staff/fila/?tab=novos` | `secretaria1` | Pedidos novos |
| 14 | Fila (crédito) | `/pedidos/staff/fila/` | `credito1` | Pedidos na etapa crédito |
| 15 | Fila (registo) | `/pedidos/staff/fila/` | `registo1` | Pedidos na etapa registo |
| 16 | Detalhe staff | `/pedidos/staff/<pk>/` | `secretaria1` / `admin` | Detalhe + acções (aprovar, indeferir, pronto, entregue) |
| 17 | Pesquisa | `/pedidos/staff/pesquisa/` | `secretaria1` / `admin` | Filtros + resultados |
| 18 | Painel | `/painel/` | `secretaria1` / `admin` | Cartões, gráficos, tempo médio |
| 19 | Erro 403 | (acesso sem permissão) | `credito1` a `/painel/` | "Acesso negado" com tema UCM |
| 20 | Erro 404 | `/esta-pagina-nao-existe/` | — | "Página não encontrada" com tema UCM |

## 11.2 Roteiro de vídeo de demonstração (fluxo completo)

Passos numerados para gravar um vídeo do fluxo completo de um requerimento:

1. Iniciar o servidor (`python manage.py runserver`) após `migrate` e `seed_demo`.
2. Fazer login como `estudante1` (`demo123`).
3. Completar o perfil académico (escolher um curso), se necessário.
4. Aceder a "Novo pedido", escolher um tipo de documento e observar o resumo
   da taxa (base, IVA, total) atualizar via HTMX.
5. Anexar cópia do BI e comprovativo de pagamento; submeter o pedido.
6. Anotar o protocolo gerado (`REQ-AAAA-NNNNN`) e o valor total.
7. Aceder a "Meus pedidos" e verificar que o pedido aparece em "Em tratamento".
8. Ver o detalhe do pedido (estado, etapa, anexos).
9. Fazer logout e entrar como `secretaria1`.
10. Abrir a fila de novos pedidos; abrir o detalhe do pedido do estudante.
11. Aprovar a etapa (avança para crédito).
12. Entrar como `credito1`; abrir a fila do crédito; ver o valor esperado e o
    comprovativo; aprovar (avança para registo ou secretaria final).
13. Entrar como `registo1` (se o tipo exigir registo académico); aprovar.
14. Entrar como `secretaria1`; fila de assinatura; marcar como pronto.
15. Ver a notificação de "pronto" (email no console, backend console).
16. Qualquer staff: marcar como entregue.
17. Entrar como `estudante1`; verificar que o pedido agora está "Entregue".
18. Aceder ao painel como `secretaria1` ou `admin`; verificar cartões e gráficos.
19. Tentar aceder a `/painel/` como `credito1`; verificar que dá 403 com tema UCM.
20. Executar `python manage.py fazer_backup --manter 7`; verificar o ZIP criado.

---
*Todos os factos são extraídos do código real do projecto.*