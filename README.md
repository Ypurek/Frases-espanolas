# Frases

A small FastAPI + SQLite app for learning Spanish phrases with Ukrainian translations.

## Environment variables

- `ADMIN_KEY` (required for admin): the secret key you type into "Admin login" on the main menu.
- `DB_PATH` (optional): path to the SQLite file. Defaults to `data.db` in the project root. The folder must be writable.

## CSV

- Anyone can download all phrases at `/phrases.csv` (UTF-8 with BOM, opens in Excel).
- Admins can import at `/admin/import`. It uses the same columns (`phrase, translation, note, example`), accepts comma, semicolon or tab separators, shows a preview with skipped rows and reasons, and only **adds** rows after you confirm. Rows whose exact phrase + translation already exist are skipped. Limits: 2 MB, 5000 rows.

## Run locally (uv)

```powershell
uv sync
$env:ADMIN_KEY = "change-me"; uv run uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000.

## Tests

```powershell
uv run pytest -q
```

## Dependencies

Managed with uv in `pyproject.toml` / `uv.lock`. cPanel has no uv, so after changing dependencies regenerate the pip file it uses:

```powershell
uv export --no-dev --no-hashes -o requirements.txt
```

## Deploy to cPanel

1. Upload the project (without `.venv` and `data.db`).
2. In **Setup Python App**, create an app with this folder as the application root and `passenger_wsgi.py` as the startup file.
3. Add `ADMIN_KEY` (and optionally `DB_PATH`) in the app's environment variables.
4. Run `pip install -r requirements.txt` in the app's virtualenv, then restart the app.

FastAPI is ASGI; `a2wsgi` wraps it as the WSGI `application` that Passenger imports.
