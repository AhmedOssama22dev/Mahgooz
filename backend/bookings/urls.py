from django.urls import path

from .views import (
    BookingDetailView,
    BookingListView,
    BookingStatusView,
    CheckoutView,
    CourtListView,
    HoldView,
    PublicPassView,
    SlotListView,
    StaffBookingListView,
    StaffLoginView,
    StaffPassView,
    StaffRedeemView,
)

urlpatterns = [
    path("courts", CourtListView.as_view(), name="courts"),
    path("slots", SlotListView.as_view(), name="slots"),
    path("passes/<str:code>", PublicPassView.as_view(), name="public-pass"),
    path("bookings/hold", HoldView.as_view(), name="booking-hold"),
    path("bookings", BookingListView.as_view(), name="booking-list"),
    path("bookings/<uuid:booking_id>", BookingDetailView.as_view(), name="booking-detail"),
    path(
        "bookings/<uuid:booking_id>/checkout",
        CheckoutView.as_view(),
        name="booking-checkout",
    ),
    path(
        "bookings/<uuid:booking_id>/status",
        BookingStatusView.as_view(),
        name="booking-status",
    ),
    path("staff/login", StaffLoginView.as_view(), name="staff-login"),
    path("staff/bookings", StaffBookingListView.as_view(), name="staff-bookings"),
    path("staff/passes/<str:code>", StaffPassView.as_view(), name="staff-pass"),
    path(
        "staff/passes/<str:code>/redeem",
        StaffRedeemView.as_view(),
        name="staff-redeem",
    ),
]
