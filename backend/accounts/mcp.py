from django.conf import settings
from django.db import connection
from mcp_server import MCPToolset


class MahgoozTools(MCPToolset):
    """Development tools for the Mahgooz Django app."""

    def health(self) -> dict:
        """Return Django process and database health."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return {
            "status": "ok",
            "debug": settings.DEBUG,
            "time_zone": settings.TIME_ZONE,
        }
