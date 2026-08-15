# Mahgouz — Stitch Design Project

> AI-generated UI for **all pages**, **mobile + desktop**, **light + dark**.  
> See **[screen-matrix.md](./screen-matrix.md)** for the full 60-screen overview.

## Project

| Item | Value |
|------|-------|
| **Stitch project** | Mahgouz |
| **Project ID** | `7191702240633724843` |
| **Open in Stitch** | [stitch.withgoogle.com](https://stitch.withgoogle.com) |
| **Design system** | `assets/e03cc309c60b436bbc38e48fd719a96f` |

### Brand tokens

| Token | Value |
|-------|-------|
| Primary green | `#1B7A4E` |
| Clay orange | `#E86A2A` |
| Light bg / surface | `#F4F7F5` / `#FFFFFF` |
| Dark bg / surface | `#0F1A14` / `#1A2620` |

Accents **never change** between light and dark — only surfaces invert.

---

## Screen matrix (60 total)

**15 pages × 4 variants** (mobile/desktop × light/dark)

### Customer (11 pages)

| Page | Route |
|------|-------|
| Landing | `/` |
| Login | `/login` |
| Register | `/register` |
| Book — date | `/book` step 1 |
| Book — court | `/book` step 2 |
| Book — slots | `/book` step 3 |
| Book — confirm | `/book` step 4 |
| Payment pending | `/book/pending` |
| Payment failed | `/book/failed` |
| My bookings | `/bookings` |
| Booking pass | `/pass/{code}` |

### Staff (4 pages)

| Page | Route | Purpose |
|------|-------|---------|
| Staff PIN login | `/staff/login` | Gate |
| **Today's bookings** | `/staff/bookings` | **Admin list — manage arrivals** |
| Lookup | `/staff` | Search by code |
| Redeem | `/staff/pass/{code}` | Check-in |

Label pattern: `{pageId}-{mobile|desktop}-{light|dark}`  
Example: `staff-bookings-desktop-light`

---

## Generation

**Script:** `scripts/stitch-generate-matrix.sh`  
**Prompts:** `docs/stitch/prompts.json`  
**Progress:** `docs/stitch/manifest.json` (resume-safe)  
**Log:** `docs/stitch/generation.log`  
**Final list:** `docs/stitch/screens-final.json`

```bash
bash scripts/stitch-generate-matrix.sh
tail -f docs/stitch/generation.log
```

Check manifest:

```bash
jq '.done | length' docs/stitch/manifest.json
```

List Stitch screens:

```bash
source .env && npx @_davideast/stitch-mcp tool list_screens \
  -d '{"projectId":"7191702240633724843"}'
```

Each screen ≈ **1–2 minutes**. Full batch ≈ **2 hours**.

### Already generated

- `landing-mobile-light` ✓
- `login-mobile-light` ✓

---

## MCP setup (Cursor)

`.cursor/mcp.json` → `.cursor/run-stitch-mcp.sh` loads `STITCH_API_KEY` from `.env`.

---

*See also: [pages-and-ui-design.md](../pages-and-ui-design.md) · [branding.md](../branding.md)*
