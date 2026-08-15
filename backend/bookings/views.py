from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCustomer, IsStaff
from bookings import errors
from bookings.availability import build_slot_grid
from bookings.expiry import expire_elapsed_holds
from bookings.hold import cancel_booking, create_hold, get_owned_booking, get_public_pass
from bookings.models import Booking, Court
from bookings.policies import assert_bookable_date, booking_sort_key, cairo_today, partition_my_bookings
from bookings.serializers import (
    BookingStatusSerializer,
    CourtSerializer,
    CustomerBookingDetailSerializer,
    CustomerBookingListItemSerializer,
    CustomerBookingSerializer,
    HoldRequestSerializer,
    PublicPassSerializer,
    SlotGridSerializer,
    SlotQuerySerializer,
    StaffBookingListItemSerializer,
    StaffDateQuerySerializer,
    StaffPassSerializer,
)
from bookings.staff import get_staff_pass, list_staff_bookings, redeem_pass
from config.exceptions import _as_details
from payments.checkout import start_checkout


class CourtListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, _request):
        courts = Court.objects.all()
        return Response(CourtSerializer(courts, many=True).data)


class SlotListView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        query = SlotQuerySerializer(data=request.query_params)
        if not query.is_valid():
            errors.invalid_query(_as_details(query.errors))
        slot_date = query.validated_data["date"]
        court_id = query.validated_data["court_id"]
        assert_bookable_date(slot_date)
        try:
            court = Court.objects.get(pk=court_id)
        except Court.DoesNotExist:
            errors.not_found("Court not found.")
        expire_elapsed_holds()
        return Response(SlotGridSerializer(build_slot_grid(court, slot_date)).data)


class PublicPassView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, _request, code):
        booking = get_public_pass(code)
        return Response(PublicPassSerializer(booking).data)


class HoldView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request):
        serializer = HoldRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = create_hold(
            user=request.user,
            slots=serializer.validated_data["slots"],
            attendee_names=serializer.validated_data["attendee_names"],
        )
        return Response(
            CustomerBookingSerializer(booking).data,
            status=status.HTTP_201_CREATED,
        )


class BookingListView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        expire_elapsed_holds()
        bookings = Booking.objects.filter(user=request.user).prefetch_related("slots__court")
        upcoming, past = partition_my_bookings(bookings)
        upcoming.sort(key=booking_sort_key)
        past.sort(key=booking_sort_key, reverse=True)
        return Response(
            {
                "upcoming": CustomerBookingListItemSerializer(upcoming, many=True).data,
                "past": CustomerBookingListItemSerializer(past, many=True).data,
            }
        )


class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request, booking_id):
        booking = get_owned_booking(user=request.user, booking_id=booking_id)
        return Response(CustomerBookingDetailSerializer(booking).data)

    def delete(self, request, booking_id):
        booking = cancel_booking(user=request.user, booking_id=booking_id)
        return Response(
            {
                "id": str(booking.id),
                "status": booking.status,
                "message": "Slot released.",
            }
        )


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request, booking_id):
        return Response(start_checkout(user=request.user, booking_id=booking_id))


class BookingStatusView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request, booking_id):
        booking = get_owned_booking(user=request.user, booking_id=booking_id)
        return Response(BookingStatusSerializer(booking).data)


class StaffBookingListView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):
        query = StaffDateQuerySerializer(data=request.query_params)
        if not query.is_valid():
            errors.invalid_query(_as_details(query.errors))
        slot_date = query.validated_data.get("date") or cairo_today()
        bookings = list_staff_bookings(slot_date)
        return Response(
            {
                "date": slot_date,
                "bookings": StaffBookingListItemSerializer(bookings, many=True).data,
            }
        )


class StaffPassView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, _request, code):
        booking = get_staff_pass(code)
        return Response(StaffPassSerializer(booking).data)


class StaffRedeemView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def post(self, _request, code):
        booking = redeem_pass(code)
        return Response(StaffPassSerializer(booking).data)
