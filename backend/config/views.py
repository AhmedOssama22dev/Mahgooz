import logging

from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.exceptions import envelope

logger = logging.getLogger(__name__)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, _request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            logger.exception("Health check database probe failed")
            return Response(
                envelope("UNHEALTHY", "Database unavailable"),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"status": "ok"})
