## Quick summary

This is a small Flask-based personal finance app. The main web server and most routes live in `app.py`. The app uses SQLite (`finance.db`), Flask-Login for auth, and server-rendered Jinja2 templates in `templates/`.

## Architecture & important files

- `app.py` — single-entry Flask app. Defines routes (login, register, dashboard, adicionar/editar/excluir transações) and also creates/configures the database with `SQLAlchemy(app)`.
- `database.py` — exports `db = SQLAlchemy()` (uninitialized). Some model modules import this pattern (`models.py`, `models_finance.py`), but note `app.py` currently creates its own `db` and model classes as well (see duplication note below).
- `models.py`, `models_finance.py` — alternative modular model definitions that expect `database.db`. They define `User` and `Transacao` models similar to the ones declared inline in `app.py`.
- `templates/` — Jinja2 templates. `base.html` contains the app's flash-message pattern and content blocks used site-wide.
- `static/` — static assets (CSS under `static/css/style.css`).
- `requirements.txt` — runtime dependencies (Flask, Flask-Login, Flask-SQLAlchemy, Werkzeug).

## Key conventions and gotchas for code changes

- Language: identifiers, templates and messages are in Portuguese (e.g. `nome`, `senha`, `transacoes`). Keep wording consistent when editing templates or routes.
- Model duplication: there are two patterns present: (A) `app.py` defines `db = SQLAlchemy(app)` and models inline; (B) `database.py` exposes an unbound `db` and `models.py` / `models_finance.py` expect app to initialize it. Do not introduce inconsistent edits across both patterns. If refactoring to use `database.py` + `models.py`, update `app.py` to import and initialize the single `db` instance and remove the inline model definitions in `app.py` in a single atomic change.
- DB file: `finance.db` (SQLite) is created in the project root by `app.py` via `db.create_all()` inside an app context. There is no migrations setup (Alembic). Schema changes require either: run the app to auto-create simple tables, or add a migration workflow manually.
- Auth: Uses `flask_login`. Passwords are stored via Werkzeug `generate_password_hash` and validated with `check_password_hash` — prefer using `set_password` / `check_password` helpers present on the `User` model.
- Flash categories: the app uses categories like `success`, `danger`, `info`, `warning`. `base.html` iterates `get_flashed_messages(with_categories=true)` — match these categories for styling.
- Transaction `tipo` values: code expects `'entrada'` or `'saida'`. Keep that spelling when adding business logic or validation.

## How to run & debug locally (Windows PowerShell)

- Install deps: `pip install -r requirements.txt` (use your venv).
- Start dev server: run `python app.py`. The app runs with `debug=True` by default.
- Database creation: running the app will create `finance.db` if missing.

## Examples of common edits

- Add a route that needs DB access: import `db` from `database.py` only if `app.py` has been refactored to initialize that instance. Otherwise modify models in `app.py` (small change) or perform a refactor first to avoid duplicate models.
- Changing templates: use `templates/base.html` flash block as canonical example for messages. Use `{{ url_for('static', filename='css/style.css') }}` for static links.

## Integration points & external behavior

- Local SQLite file `finance.db` (no external DB).
- Flask-Login session cookies — standard behavior; no OAuth integrations.

## Safety notes for automated edits

- Avoid simultaneously editing both inline models in `app.py` and modular `models.py` files without fully migrating the app to a single model pattern.
- Because there are no tests or migrations, prefer small, reversible edits and manual verification by running the app.

## Where to look for examples in this repo

- Routes and CRUD flows: `app.py` (search for `@app.route` handlers like `/adicionar`, `/editar/<int:id>`, `/excluir/<int:id>`).
- Model fields & password helpers: `models.py` and the `User` class inside `app.py`.
- Template/layout patterns: `templates/base.html` and `templates/dashboard.html`.

If anything here is unclear or you want the file to include additional rules (e.g., preferred refactor path or a test harness), tell me which sections to expand and I will update the file.

## Plano de refatoração: unificar modelos (opção recomendada)

Resumo rápido: atualmente há duplicação — `app.py` define `db = SQLAlchemy(app)` e declara `User`/`Transacao` inline; `database.py` exporta `db = SQLAlchemy()` e `models.py`/`models_finance.py` esperam esse `db`. Refatorar para usar o padrão modular reduz duplicação e facilita testes.

Passos seguros (faça um branch antes):
1. Criar branch: `git checkout -b refactor/unify-models`.
2. Fazer backup do DB: copie `finance.db` para `finance.db.bak`.
3. No `app.py` substitua a linha `db = SQLAlchemy(app)` por `from database import db` e, após criar `app`, inicialize com `db.init_app(app)`.
4. Mova/remova as classes `User` e `Transacao` de `app.py` e importe-as de `models.py` / `models_finance.py` (ex.: `from models import User` e `from models_finance import Transacao`).
5. Mantenha o trecho `with app.app_context(): db.create_all()` para recriar tabelas locais após a mudança.
6. Teste: crie um usuário via rota `/register` e verifique `dashboard` e CRUD de transações.
7. Commit e PR: escreva uma breve descrição do que foi unificado e por que.

Notas e riscos:
- Sem migrações formais (Alembic), mudanças de esquema podem exigir recriar o DB ou escrever scripts de migração manuais. Por isso o backup é obrigatório.
- Teste manualmente páginas de login/registro/CRUD após a unificação.

## Comandos PowerShell rápidos (setup & execução)

Abra o PowerShell na raiz do repositório e execute (passo-a-passo):

```powershell
# criar e ativar venv (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# instalar dependências
pip install -r requirements.txt

# iniciar servidor (dev)
python app.py

# opcional: remover banco local (permanente)
Remove-Item -Path .\finance.db -Force
```

Use os comandos acima para reproduzir o ambiente localmente. Se preferir CMD.exe ou Git Bash, adapte o comando de ativação do venv.
