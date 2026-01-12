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

- Language: identifiers, templates, and messages are in Portuguese (e.g., `nome`, `senha`, `transacoes`). Keep wording consistent when editing templates or routes.
- Model duplication: there are two patterns present: (A) `app.py` defines `db = SQLAlchemy(app)` and models inline; (B) `database.py` exposes an unbound `db` and `models.py` / `models_finance.py` expect app to initialize it. Do not introduce inconsistent edits across both patterns. If refactoring to use `database.py` + `models.py`, update `app.py` to import and initialize the single `db` instance and remove the inline model definitions in `app.py` in a single atomic change.
- DB file: `finance.db` (SQLite) is created in the project root by `app.py` via `db.create_all()` inside an app context. There is no migrations setup (Alembic). Schema changes require either: run the app to auto-create simple tables, or add a migration workflow manually.
- Auth: Uses `flask_login`. Passwords are stored via Werkzeug `generate_password_hash` and validated with `check_password_hash` — prefer using `set_password` / `check_password` helpers present on the `User` model.
- Flash categories: the app uses categories like `success`, `danger`, `info`, `warning`. `base.html` iterates `get_flashed_messages(with_categories=true)` — match these categories for styling.
- Transaction `tipo` values: code expects `'entrada'` or `'saida'`. Keep that spelling when adding business logic or validation.

## Frontend-specific conventions

- Templates: Ensure proper use of `{{ url_for('static', filename='...') }}` for assets. Check that forms include `method="post"` where applicable.
- Flash messages: Use the block in `templates/base.html` as the canonical example.
- Responsiveness: Verify `static/css/style.css` for layout consistency and responsiveness.
- Examples:
  - `templates/dashboard.html` — Example of listing `transacoes`.
  - `templates/base.html` — Flash messages and CSS inclusion.

## Backend-specific conventions

- Models: Avoid duplication between `app.py` and `models.py`/`models_finance.py`. Use `database.db.init_app(app)` for initialization.
- Business rules:
  - `Transacao.tipo` must be `entrada` or `saida`.
  - Permissions: Only the owner can edit/delete (`transacao.user_id == current_user.id`).
- Examples:
  - `app.py` — Routes and CRUD logic.
  - `models.py` / `models_finance.py` — Modular definitions of `User` and `Transacao`.

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

## Refactoring plan: unify models (recommended option)

Currently, there is duplication — `app.py` defines `db = SQLAlchemy(app)` and declares `User`/`Transacao` inline; `database.py` exports `db = SQLAlchemy()` and `models.py`/`models_finance.py` expect this `db`. Refactoring to use the modular pattern reduces duplication and facilitates testing.

Safe steps (create a branch first):
1. Create branch: `git checkout -b refactor/unify-models`.
2. Backup DB: copy `finance.db` to `finance.db.bak`.
3. In `app.py`, replace `db = SQLAlchemy(app)` with `from database import db` and, after creating `app`, initialize with `db.init_app(app)`.
4. Move/remove the `User` and `Transacao` classes from `app.py` and import them from `models.py` / `models_finance.py` (e.g., `from models import User` and `from models_finance import Transacao`).
5. Keep the `with app.app_context(): db.create_all()` snippet to recreate local tables after the change.
6. Test: Create a user via the `/register` route and verify the `dashboard` and transaction CRUD.
7. Commit and PR: Write a brief description of what was unified and why.

Notes and risks:
- Without formal migrations (Alembic), schema changes may require recreating the DB or writing manual migration scripts. Hence, backup is mandatory.
- Manually test login/register/CRUD pages after unification.

## Quick PowerShell commands (setup & execution)

Open PowerShell in the repository root and execute step-by-step:

```powershell
# create and activate venv (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install dependencies
pip install -r requirements.txt

# start server (dev)
python app.py

# optional: remove local database (permanent)
Remove-Item -Path .\finance.db -Force
```

Use the above commands to reproduce the local environment. If you prefer CMD.exe or Git Bash, adapt the venv activation command.
