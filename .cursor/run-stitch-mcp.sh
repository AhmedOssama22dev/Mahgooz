#!/usr/bin/env bash
# ponytail: loads STITCH_API_KEY from project .env for Cursor MCP
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a && source "$ROOT/.env" && set +a
exec npx -y @_davideast/stitch-mcp proxy
