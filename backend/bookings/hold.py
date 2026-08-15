from django.conf import settings
from django.db import IntegrityError, transaction

from bookings import errors
from bookings.expiry import expire_elapsed_holds
from bookings.models import Booking, BookingSlot
from bookings.policies import (
    PAID_PASS_STATUSES,
    assert_transition,
    cairo_now,
    can_cancel,
    format_hhmm,
    normalize_hold_slots,
    slot_totals,
)

ACTIVE_SLOT_CONSTRAINT = "uniq_active_court_slot"
PAID_STATUSES = {Booking.Status.CONFIRMED, Booking.Status.REDEEMED}


def is_active_slot_conflict(exc):
    cause = getattr(exc, "__cause__", None)
    diag = getattr(cause, "diag", None)
    constraint = getattr(diag, "constraint_name", None) if diag is not None else None
    if constraint == ACTIVE_SLOT_CONSTRAINT:
        return True
    return ACTIVE_SLOT_CONSTRAINT in str(exc)


def _conflicting_slots(normalized):
    court = normalized[0]["court"]
    slot_date = normalized[0]["date"]
    starts = [row["start_time"] for row in normalized]
    taken = set(
        BookingSlot.objects.filter(
            court=court,
            date=slot_date,
            start_time__in=starts,
            released_at__isnull=True,
        ).values_list("start_time", flat=True)
    )
    conflicts = [
        {
            "court_id": str(court.id),
            "date": slot_date.isoformat(),
            "start_time": format_hhmm(start),
        }
        for start in starts
        if start in taken
    ]
    if conflicts:
        return conflicts
    return [
        {
            "court_id": str(row["court"].id),
            "date": row["date"].isoformat(),
            "start_time": format_hhmm(row["start_time"]),
        }
        for row in normalized
    ]


def create_hold(*, user, slots, attendee_names, now=None):
    now = cairo_now(now)
    normalized = normalize_hold_slots(slots, now=now)
    price_egp, price_cents = slot_totals(normalized)
    expire_elapsed_holds(now=now)
    try:
        with transaction.atomic():
            booking = Booking.objects.create(
                user=user,
                status=Booking.Status.HELD,
                booker_name=user.name,
                attendee_names=attendee_names,
                total_price_egp=price_egp,
                total_price_cents=price_cents,
                hold_expires_at=now + settings.HOLD_TTL,
            )
            BookingSlot.objects.bulk_create(
                [
                    BookingSlot(
                        booking=booking,
                        court=row["court"],
                        date=row["date"],
                        start_time=row["start_time"],
                        price_egp=row["price_egp"],
                        price_cents=row["price_cents"],
                    )
                    for row in normalized
                ]
            )
    except IntegrityError as exc:
        if not is_active_slot_conflict(exc):
            raise
        errors.slot_taken(_conflicting_slots(normalized))
    return booking


def get_owned_booking(*, user, booking_id, now=None):
    now = cairo_now(now)
    expire_elapsed_holds(now=now)
    try:
        booking = Booking.objects.prefetch_related("slots__court").get(pk=booking_id)
    except Booking.DoesNotExist:
        errors.not_found("Booking not found.")
    if booking.user_id != user.id:
        errors.forbidden("You do not own this booking.")
    return booking


def get_public_pass(code):
    if not isinstance(code, str) or not code.strip():
        errors.not_found("No paid booking for this code.")
    booking = (
        Booking.objects.prefetch_related("slots__court")
        .filter(booking_code__iexact=code.strip())
        .first()
    )
    if booking is None or booking.status not in PAID_PASS_STATUSES:
        errors.not_found("No paid booking for this code.")
    return booking


def cancel_booking(*, user, booking_id, now=None):
    now = cairo_now(now)
    expire_elapsed_holds(now=now)
    with transaction.atomic():
        try:
            booking = Booking.objects.select_for_update().get(pk=booking_id)
        except Booking.DoesNotExist:
            errors.not_found("Booking not found.")
        if booking.user_id != user.id:
            errors.forbidden("You do not own this booking.")
        if booking.status == Booking.Status.EXPIRED:
            errors.hold_expired()
        if not can_cancel(booking):
            if booking.status in PAID_STATUSES:
                errors.cannot_cancel(
                    "Paid bookings cannot be cancelled in MVP (no refunds)."
                )
            errors.cannot_cancel()
        assert_transition(booking, Booking.Status.CANCELLED)
        booking.status = Booking.Status.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        booking.slots.filter(released_at__isnull=True).update(released_at=now)
    return booking
