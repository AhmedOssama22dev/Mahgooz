from datetime import datetime, time

from django.conf import settings


def _as_time(start):
    if isinstance(start, time):
        return start
    if isinstance(start, str):
        return datetime.strptime(start, "%H:%M").time()
    raise TypeError("start_time must be datetime.time or HH:MM string")


def price_for_start_time(start):
    """Return the configured price band for a 60-minute slot start time."""
    start = _as_time(start)
    for band in settings.BOOKING_PRICE_BANDS:
        if band["start"] <= start < band["end"]:
            price_egp = band["price_egp"]
            return {
                "period": band["period"],
                "price_egp": price_egp,
                "price_cents": price_egp * 100,
                "label": band.get("label") or "",
            }
    raise ValueError(f"No price band for start time {start.strftime('%H:%M')}")
