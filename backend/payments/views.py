from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from bookings import errors


class PaymobWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, _request):
        errors.not_implemented()
