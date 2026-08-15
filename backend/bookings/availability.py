from django.conf import settings

from bookings.models import Booking, BookingSlot
from bookings.policies import end_time_for, format_hhmm, start_time_grid
from bookings.pricing import price_for_start_time

HELD_STATUSES = {
    Booking.Status.HELD,
    Booking.Status.PENDING_PAYMENT,
}


def _grid_state(status):
    if status in HELD_STATUSES:
        return "held"
    return "booked"


def build_slot_grid(court, date):
    occupied = {
        slot.start_time: slot.booking.status
        for slot in BookingSlot.objects.filter(
            court=court,
            date=date,
            released_at__isnull=True,
        ).select_related("booking")
    }
    slots = []
    for start in start_time_grid():
        pricing = price_for_start_time(start)
        status = occupied.get(start)
        slots.append(
            {
                "start_time": format_hhmm(start),
                "end_time": format_hhmm(end_time_for(start)),
                "state": _grid_state(status) if status is not None else "available",
                "period": pricing["period"],
                "price_egp": pricing["price_egp"],
                "price_cents": pricing["price_cents"],
                "label": pricing["label"] or None,
            }
        )
    return {
        "date": date,
        "court": {"id": court.id, "name": court.name},
        "operating_hours": {
            "open": format_hhmm(settings.BOOKING_OPERATING_START),
            "close": format_hhmm(settings.BOOKING_OPERATING_END),
        },
        "slot_minutes": settings.BOOKING_SLOT_DURATION_MINUTES,
        "slots": slots,
    }
