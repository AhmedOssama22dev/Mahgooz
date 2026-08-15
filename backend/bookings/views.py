from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer, IsStaff
from bookings import errors
from bookings.models import Court
from bookings.serializers import CourtSerializer


class CourtListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, _request):
        courts = Court.objects.all()
        return Response(CourtSerializer(courts, many=True).data)


class SlotListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, _request):
        errors.not_implemented()


class PublicPassView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, _request, code):
        errors.not_implemented()


class HoldView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, _request):
        errors.not_implemented()


class BookingListView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, _request):
        errors.not_implemented()


class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, _request, booking_id):
        errors.not_implemented()

    def delete(self, _request, booking_id):
        errors.not_implemented()


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, _request, booking_id):
        errors.not_implemented()


class BookingStatusView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, _request, booking_id):
        errors.not_implemented()


class StaffLoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, _request):
        errors.not_implemented()


class StaffBookingListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, _request):
        errors.not_implemented()


class StaffPassView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, _request, code):
        errors.not_implemented()


class StaffRedeemView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def post(self, _request, code):
        errors.not_implemented()
