# Mahgooz

Padel court booking: Pay, reserve, redeem. Django API in `backend/`, React in `frontend/`.

## Install and run

Requires Python 3.10+ and Docker.

Start PostgreSQL from the project root:

```bash
docker compose up -d db
```

Set up Django:

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

App: http://127.0.0.1:8000/api/v1/health

The default development database settings are in `backend/.env.example` and
match `compose.yaml`. PostgreSQL data is kept in the `postgres_data` Docker
volume. To open a PostgreSQL shell:

```bash
docker compose exec db psql -U mahgooz -d mahgooz
```

## MCP server

`django-mcp-server` is included in `backend/requirements.txt` (installed with the steps above).

1. Reload Cursor.
2. Enable the **django** MCP server (the repo already has `.cursor/mcp.json`).

With `runserver` running: http://127.0.0.1:8000/mcp

Check tools:

```bash
python manage.py mcp_inspect
```
