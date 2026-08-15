from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.exceptions import APIError
from payments.webhook import process_paymob_callback


class PaymobWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def handle_exception(self, exc):
        if isinstance(exc, ParseError):
            exc = APIError(
                "INVALID_HMAC",
                "Callback HMAC verification failed.",
                status.HTTP_401_UNAUTHORIZED,
            )
        return super().handle_exception(exc)

    def post(self, request):
        received_hmac = request.query_params.get("hmac") or ""
        body = request.data
        if isinstance(body, dict) and not received_hmac:
            received_hmac = str(body.get("hmac") or "")
        return Response(process_paymob_callback(body=body, received_hmac=received_hmac))
