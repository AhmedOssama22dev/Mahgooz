# Backend

Django project (`config`) with apps `accounts`, `bookings`, and `payments`. Python 3.10+ and PostgreSQL 17.

## Install and run

From the repository root, start PostgreSQL:

```bash
docker compose up -d db
```

Then create the Python environment:

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

http://127.0.0.1:8000/api/v1/health

`migrate` seeds **Court 1** and **Court 2**. Re-run with `python manage.py seed_courts` if needed.

Unpaid holds past the 10-minute TTL are released lazily on `GET /slots`. Run `python manage.py expire_holds` for demo/ops cleanup.

## Booking rules

One booking can cover one or more 60-minute hours on the same court and date. A slot occupies the court while `released_at` is null (Postgres unique index `uniq_active_court_slot`).

| Rule | Value |
|------|--------|
| Operating hours | 08:00–22:00 (last start 21:00) |
| Slot duration | 60 minutes |
| Book-ahead window | 14 days (`BOOKING_WINDOW_DAYS`) |
| Hold TTL | 10 minutes (`HOLD_TTL_MINUTES`) |
| Morning | 08:00–12:00 · EGP 200 |
| Afternoon | 12:00–17:00 · EGP 280 |
| Evening | 17:00–22:00 · EGP 350 |

The values in `.env.example` match the Docker database. Open `psql` with:

```bash
docker compose exec db psql -U mahgooz -d mahgooz
```

## MCP server

Installed with `pip install -r requirements.txt`.

Cursor: reload the window and enable **django** (config is `.cursor/mcp.json` in the repo).

HTTP (while `runserver` is up): http://127.0.0.1:8000/mcp

```bash
python manage.py mcp_inspect
```
