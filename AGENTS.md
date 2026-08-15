# Mahgooz (CourtPass) — Agent Instructions

Padel court booking app for Mostafa's two courts in Sheikh Zayed, Egypt.

**Core mechanic:** Pay → Reserve → Redeem

## Stack

- **Backend:** Django + Django REST Framework (`backend/`)
- **Frontend:** React + TypeScript + shadcn/ui
- **Auth:** phone + password (Egyptian mobile `01xxxxxxxxx`)
- **Payments:** Paymob Intention API + Unified Checkout + HMAC webhooks
- **MCP:** django-mcp-server (`mcp_server`) — live docs via `.cursor/skills/django-mcp-server/`

## Key docs (read before implementing)

| Doc | Purpose |
|-----|---------|
| `docs/pages-and-ui-design.md` | Pages, UI, flows, branding, component map, MVP build order |
| `.cursor/skills/django-mcp-server/SKILL.md` | Fetch live django-mcp-server README before MCP work |
| `backend/requirements.md` | Backend requirements |
| `frontend/requirements.md` | Frontend requirements |

## Project conventions

- Mobile-first UI at 390px; `max-w-md mx-auto` for layout
- Slot states: `available` | `held` | `booked` | `selected`
- Hold TTL: 10 minutes; poll interval: 2s on pending page
- Court labels: **Court 1** / **Court 2**
- Paymob webhook (`POST /webhooks/paymob`) is the source of truth — never confirm payment from redirect alone
- Use `.cursor/skills/paymob-integration/` for all Paymob integration work
- For Django MCP tools, follow `.cursor/skills/django-mcp-server/` (fetch the GitHub README; do not use stale APIs)

## Scope guard (do NOT build unless asked)

SMS OTP, Google/social login, refunds UI, SMS/WhatsApp notifications, dynamic pricing engine, multi-location, native mobile app, AI features

## MVP build order

1. Django auth + phone login/register
2. Landing + auth-aware header
3. Book wizard Steps 1–3 with slot data
4. Hold/release API + slot states
5. Confirm step + Paymob redirect
6. Webhook + pending poll + pass page
7. `/bookings` list
8. Staff lookup + redeem
9. Polish: bottom nav, morning pricing badges, landing availability
