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

Fill Paymob **test-mode** keys in `.env` (`PAYMOB_SECRET_KEY`, `PAYMOB_PUBLIC_KEY`, `PAYMOB_HMAC_SECRET`, `PAYMOB_INTEGRATION_ID_CARD`). Leave them empty only for local tests that mock Paymob.

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_staff
python manage.py runserver
```

http://127.0.0.1:8000/api/v1/health

`migrate` seeds **Court 1** and **Court 2**. Re-run with `python manage.py seed_courts` if needed.

Staff use the same phone + password login as customers. There is no staff PIN. Mark a user as staff in Django admin (`is_staff`), or seed the demo desk account from `.env`:

```bash
python manage.py seed_staff
```

Unpaid holds past the 10-minute TTL are released lazily on `GET /slots`. Run `python manage.py expire_holds` for demo/ops cleanup.

## Tests

From `backend/` with Postgres running:

```bash
python manage.py test
```

The suite uses a PostgreSQL test database (`test_mahgooz`).

## Postman

Import:

- [`postman/Mahgooz_API.postman_collection.json`](postman/Mahgooz_API.postman_collection.json)
- [`postman/Mahgooz_Local.postman_environment.json`](postman/Mahgooz_Local.postman_environment.json)

Runnable folder order: health/courts → customer login → `slots[]` hold → checkout → poll + public pass → staff `/auth/login` → lookup/redeem → invalid webhook.

Regenerate after API shape changes:

```bash
python postman/generate.py
```

Environment variables include `staff_phone` and `staff_password` (no `staff_token`). Hold requests use `slots[]`.

## Tunnel and webhook registration

Paymob must reach `POST /api/v1/webhooks/paymob`. Localhost is not enough.

1. Start the API: `python manage.py runserver`
2. Expose it, for example `ngrok http 8000` or Cloudflare Tunnel
3. Set `PUBLIC_API_URL` to the public origin (no trailing slash), e.g. `https://abc123.ngrok-free.app`
4. Add the tunnel hostname to `DJANGO_ALLOWED_HOSTS`
5. Restart `runserver` so checkout intentions send `notification_url={PUBLIC_API_URL}/api/v1/webhooks/paymob`

Checkout creates the Intention with that `notification_url`. You can also paste the same URL in the Paymob Dashboard webhook settings. HMAC-SHA512 verification is required; a forged callback returns `401 INVALID_HMAC` and does not change the booking.

After a test-card payment, poll `GET /bookings/{id}/status` until `confirmed`. The browser redirect is never treated as paid.

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
