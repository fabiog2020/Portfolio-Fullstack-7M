## Agente Backend — responsabilidades

- Verificar consistência de modelos (evitar duplicação entre `app.py` e `models.py`/`models_finance.py`).
- Checar uso do `db` (inicialização via `database.db.init_app(app)` quando aplicável).
- Validar regras de negócio críticas:
  - `Transacao.tipo` deve ser `entrada` ou `saida`.
  - Permissões: somente o dono pode editar/excluir (`transacao.user_id == current_user.id`).

## Checks automáticos sugeridos
- Detectar classes de modelo duplicadas (mesmo nome/fields em mais de um arquivo).
- Procurar chamadas de `db.create_all()` fora de um `app.app_context()`.

## Exemplos no repo
- `app.py` — rotas e lógica de CRUD.
- `models.py` / `models_finance.py` — definição modular de `User` e `Transacao`.

Use este arquivo para orientar revisões backend e automações que chequem integridade do modelo e segurança básica.
