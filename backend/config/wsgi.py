import os

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def _apply_schema_on_boot():
    """Create tables when Railway starts gunicorn without a migrate step."""
    if not os.environ.get("RAILWAY_ENVIRONMENT"):
        return
    django.setup()
    call_command("ensure_schema")


_apply_schema_on_boot()
application = get_wsgi_application()
