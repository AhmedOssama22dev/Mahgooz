from bookings import errors
from bookings.models import Booking
from bookings.policies import (
    PAID_PASS_STATUSES,
    booking_slot_date,
    booking_sort_key,
    cairo_now,
    cairo_today,
    format_hhmm,
)

UNPAID_LOOKUP_STATUSES = {
    Booking.Status.HELD,
    Booking.Status.PENDING_PAYMENT,
    Booking.Status.FAILED,
}

PASS_NOT_FOUND = "No booking for this code."


def _normalize_code(code):
    if not isinstance(code, str) or not code.strip():
        return None
    return code.strip()


def _load_booking_by_code(code):
    normalized = _normalize_code(code)
    if normalized is None:
        return None
    return (
        Booking.objects.select_related("user")
        .prefetch_related("slots__court")
        .filter(booking_code__iexact=normalized)
        .first()
    )


def _reload_booking(booking_id):
    return (
        Booking.objects.select_related("user")
        .prefetch_related("slots__court")
        .get(pk=booking_id)
    )


def _wrong_day_message(slot_date):
    weekday = slot_date.strftime("%a")
    month_year = slot_date.strftime("%b %Y")
    return f"This pass is for {weekday} {slot_date.day} {month_year}, not today."


def _already_redeemed_message(booking):
    if booking.redeemed_at is None:
        return None
    local = cairo_now(booking.redeemed_at)
    return f"This pass was already redeemed at {format_hhmm(local.time())}."


def list_staff_bookings(slot_date):
    bookings = list(
        Booking.objects.filter(
            status__in=PAID_PASS_STATUSES,
            slots__date=slot_date,
        )
        .select_related("user")
        .prefetch_related("slots__court")
        .distinct()
    )
    bookings.sort(key=booking_sort_key)
    return bookings


def get_staff_pass(code):
    booking = _load_booking_by_code(code)
    if booking is None:
        errors.not_found(PASS_NOT_FOUND)
    if booking.status in PAID_PASS_STATUSES:
        return booking
    if booking.status in UNPAID_LOOKUP_STATUSES:
        errors.payment_not_confirmed()
    errors.not_found(PASS_NOT_FOUND)


def redeem_pass(code, now=None):
    now = cairo_now(now)
    today = cairo_today(now)
    booking = _load_booking_by_code(code)
    if booking is None:
        errors.not_found(PASS_NOT_FOUND)
    if booking.status in UNPAID_LOOKUP_STATUSES:
        errors.payment_not_confirmed()
    if booking.status not in PAID_PASS_STATUSES:
        errors.not_found(PASS_NOT_FOUND)

    slot_date = booking_slot_date(booking)
    if slot_date is not None and slot_date != today:
        errors.wrong_day(_wrong_day_message(slot_date))

    updated = Booking.objects.filter(
        pk=booking.pk,
        status=Booking.Status.CONFIRMED,
    ).update(status=Booking.Status.REDEEMED, redeemed_at=now)
    if updated != 1:
        booking = _reload_booking(booking.pk)
        errors.already_redeemed(_already_redeemed_message(booking))
    return _reload_booking(booking.pk)
