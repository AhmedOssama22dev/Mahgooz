---
name: django-mcp-server
description: >-
  Integrates django-mcp-server (mcp_server) in the Mahgooz Django backend.
  Use when adding MCP tools, ModelQueryToolset, DRF-to-MCP annotations,
  /mcp endpoint settings, stdio_server, or Cursor MCP config.
---

# Django MCP Server (live docs)

Do **not** rely on memorized django-mcp-server APIs. Fetch the current README before changing MCP code.

## Live documentation (required)

1. Fetch: https://raw.githubusercontent.com/gts360/django-mcp-server/main/README.md
2. If that 404s, fetch: https://raw.githubusercontent.com/omarbenhamid/django-mcp-server/main/README.md
3. Follow that README for install, `INSTALLED_APPS`, URLs, `mcp.py` toolsets, and settings.

PyPI package: `django-mcp-server` (import package name: `mcp_server`).

## This repo

- Django project: `backend/` (`config` settings, `accounts` / `bookings` / `payments` apps)
- Tools live in `backend/accounts/mcp.py` (auto-discovered from installed apps)
- HTTP endpoint: `/mcp` (no trailing slash) when `python manage.py runserver`
- Cursor / local STDIO: `.cursor/mcp.json` runs `backend/run_mcp.py` → `manage.py stdio_server`
- Shared with anyone who clones the repo — keep `.cursor/mcp.json` committed, never put secrets in it
- Pin `mcp>=1.8.0,<2` until django-mcp-server supports MCP SDK 2.x (`FastMCP` import)

## Local checks

```bash
cd backend
.venv/Scripts/python manage.py mcp_inspect   # Windows
.venv/bin/python manage.py mcp_inspect       # macOS/Linux
```

## Project settings already used

- `mcp_server` and `rest_framework` are in `INSTALLED_APPS`
- `path("", include("mcp_server.urls"))` is in `config/urls.py`
- `DJANGO_MCP_GLOBAL_SERVER_CONFIG` and `DJANGO_MCP_ENDPOINT = "mcp"` are in `config/settings.py`

Add new tools in `accounts/mcp.py` (or another installed app's `mcp.py`). Do not copy stale examples from chat history if they disagree with the fetched README.
