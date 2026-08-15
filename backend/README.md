# Backend

Django project (`config`) with app `core`. Python 3.10+.

## Install and run

```bash
cd backend
python -m venv .venv
```

Windows: `.venv\Scripts\activate` then `copy .env.example .env`

macOS / Linux: `source .venv/bin/activate` then `cp .env.example .env`

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

http://127.0.0.1:8000/api/health/

## MCP server

Installed with `pip install -r requirements.txt`.

Cursor: reload the window and enable **django** (config is `.cursor/mcp.json` in the repo).

HTTP (while `runserver` is up): http://127.0.0.1:8000/mcp

```bash
python manage.py mcp_inspect
```
