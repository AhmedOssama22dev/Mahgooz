from django.db import transaction

from bookings.models import Booking, BookingSlot
from bookings.policies import cairo_now

UNPAID_HOLD_STATUSES = (
    Booking.Status.HELD,
    Booking.Status.PENDING_PAYMENT,
)


def expire_elapsed_holds(now=None):
    """Expire unpaid holds whose TTL has elapsed and release their slots.

    Confirmed and redeemed bookings are never expired, even if hold_expires_at
    is still set. Returns the number of parent bookings that were expired.
    """
    now = cairo_now(now)
    with transaction.atomic():
        expired_ids = list(
            Booking.objects.select_for_update()
            .filter(
                status__in=UNPAID_HOLD_STATUSES,
                hold_expires_at__lte=now,
            )
            .values_list("id", flat=True)
        )
        if not expired_ids:
            return 0
        Booking.objects.filter(id__in=expired_ids).update(status=Booking.Status.EXPIRED)
        BookingSlot.objects.filter(
            booking_id__in=expired_ids,
            released_at__isnull=True,
        ).update(released_at=now)
        return len(expired_ids)
