# 12. Limitações e trabalho futuro — secção 6.2

## 12.1 Limitações reais encontradas no código

| Limitação | Evidência no código |
| --- | --- |
| Base de dados de desenvolvimento é SQLite (não adequada para produção com vários escritores) | `config/settings.py` linha 135 (`django.db.backends.sqlite3`) |
| Cache de throttling de login usa `LocMemCache` por padrão (não partilhada entre vários processos/servidores) | `config/settings.py` linhas 148-156; comentário nas linhas 145-147 |
| Não há pagamento online; o comprovativo é apenas um ficheiro anexado e validado manualmente pelo crédito | `pedidos/validators.py`, `pedidos/views.py` `carregar_extracto` |
| Notificações por email usam backend de console por defeito; em produção requer SMTP configurado | `config/settings.py` linhas 279-282 |
| As decisões são imutáveis (não se podem alterar nem apagar), o que é intencional mas limita correções de erros | `pedidos/models.py` `Decisao.save`/`delete` (linhas 273-283) |
| Não há trilha de auditoria geral de quem acedeu a quê; apenas decisões registam autor e data | `pedidos/models.py` `Decisao` (linhas 234-283) |
| O número de estudante é extraído automaticamente do email; se não for identificável, o estudante fica bloqueado sem poder submeter pedidos | `contas/models.py` `Perfil.save` (linhas 132-153); `contas/views.py` `completar_perfil` (linhas 170-178) |
| O comando `fazer_backup` só suporta bases de dados SQLite | `pedidos/management/commands/fazer_backup.py` linhas 90-93 |
| Não há reset de palavra-passe via email (apenas login clássico e Google) | `contas/views.py` (apenas login e logout) |
| O admin do Django permite editar tipos de documento (taxas/prazos) em tempo real, o que pode afectar pedidos futuros mas não os já criados (valor congelado) | `pedidos/admin.py` `TipoDocumentoAdmin` (list_editable) |

## 12.2 Trabalho futuro plausível

| Melhoria | Justificação (baseada no código) |
| --- | --- |
| Substituir SQLite por PostgreSQL/MySQL em produção | SQLite é o engine actual (`config/settings.py` linha 135) |
| Usar cache partilhado (Redis/Memcached) para throttling em múltiplos servidores | `LocMemCache` é o default (`config/settings.py` linhas 148-156) |
| Adicionar pagamento online integrado | Actualmente só há validação manual de comprovativo (`carregar_extracto`) |
| Configurar backend de email SMTP em produção | Default é console (`config/settings.py` linha 280) |
| Adicionar trilha de auditoria de acessos | Actualmente só decisões registam autor (`pedidos/models.py` `Decisao`) |
| Adicionar reset de palavra-passe | Não existe no `contas/views.py` |
| Tornar `fazer_backup` compatível com outras bases de dados | Actualmente só SQLite (`fazer_backup.py` linhas 90-93) |
| Adicionar API REST para integração com outras plataformas | Actualmente só views renderizadas com templates |
| Adicionar testes para login Google | Não há teste dedicado para `ContasSocialAccountAdapter` |

---
*Todas as limitações são extraídas do código real do projecto; as melhorias são propostas plausíveis, não implementadas.*