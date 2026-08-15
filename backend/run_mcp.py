#!/usr/bin/env python
"""Cross-platform launcher for Django MCP stdio (Cursor / Claude Desktop)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent


def venv_python() -> Path | None:
    if os.name == "nt":
        candidate = BACKEND / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = BACKEND / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else None


def main() -> int:
    python = venv_python()
    if python is None:
        print(
            "Django MCP: create the backend venv and install deps first:\n"
            "  cd backend && python -m venv .venv && "
            ".venv/Scripts/pip install -r requirements.txt  # Windows\n"
            "  .venv/bin/pip install -r requirements.txt     # macOS/Linux",
            file=sys.stderr,
        )
        return 1
    extra = sys.argv[1:]
    cmd = [str(python), str(BACKEND / "manage.py"), "stdio_server", *extra]
    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    env["PYTHONPATH"] = str(BACKEND) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.call(cmd, cwd=BACKEND, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
