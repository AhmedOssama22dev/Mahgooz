import secrets
import string
from datetime import datetime, time, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from bookings import errors
from bookings.models import Booking, Court
from bookings.pricing import price_for_start_time

__all__ = [
    "ALLOWED_TRANSITIONS",
    "CODE_PREFIX",
    "CODE_VISIBLE_STATUSES",
    "PAID_PASS_STATUSES",
    "UPCOMING_STATUSES",
    "as_cairo_date",
    "assert_bookable_date",
    "assert_transition",
    "booking_last_slot_end",
    "booking_slot_date",
    "booking_slots_list",
    "booking_sort_key",
    "cairo_now",
    "cairo_today",
    "can_cancel",
    "can_checkout",
    "can_redeem",
    "end_time_for",
    "first_last_slots",
    "format_hhmm",
    "generate_booking_code",
    "issued_booking_code",
    "iter_start_times",
    "normalize_hold_slots",
    "partition_my_bookings",
    "pass_url",
    "price_for_start_time",
    "qr_payload",
    "slot_totals",
    "start_time_grid",
]

CODE_PREFIX = "MGZ-"
CODE_LENGTH = 5
CODE_ALPHABET = string.ascii_uppercase + string.digits

ALLOWED_TRANSITIONS = {
    Booking.Status.HELD: {
        Booking.Status.PENDING_PAYMENT,
        Booking.Status.CANCELLED,
        Booking.Status.EXPIRED,
        Booking.Status.CONFIRMED,
        Booking.Status.FAILED,
    },
    Booking.Status.PENDING_PAYMENT: {
        Booking.Status.CONFIRMED,
        Booking.Status.FAILED,
        Booking.Status.CANCELLED,
        Booking.Status.EXPIRED,
    },
    Booking.Status.CONFIRMED: {
        Booking.Status.REDEEMED,
    },
}

UPCOMING_STATUSES = {
    Booking.Status.HELD,
    Booking.Status.PENDING_PAYMENT,
    Booking.Status.CONFIRMED,
}

CODE_VISIBLE_STATUSES = {
    Booking.Status.CONFIRMED,
    Booking.Status.REDEEMED,
}

PAID_PASS_STATUSES = CODE_VISIBLE_STATUSES


def cairo_now(now=None):
    if now is None:
        now = timezone.now()
    if timezone.is_naive(now):
        now = timezone.make_aware(now, timezone.get_current_timezone())
    return timezone.localtime(now)


def cairo_today(now=None):
    return cairo_now(now).date()


def iter_start_times():
    start = settings.BOOKING_OPERATING_START
    close = settings.BOOKING_OPERATING_END
    minutes = settings.BOOKING_SLOT_DURATION_MINUTES
    current = datetime.combine(datetime.min.date(), start)
    last = datetime.combine(datetime.min.date(), close) - timedelta(minutes=minutes)
    while current <= last:
        yield current.time()
        current += timedelta(minutes=minutes)


def start_time_grid():
    return tuple(iter_start_times())


def end_time_for(start):
    if isinstance(start, str):
        start = datetime.strptime(start, "%H:%M").time()
    delta = timedelta(minutes=settings.BOOKING_SLOT_DURATION_MINUTES)
    return (datetime.combine(datetime.min.date(), start) + delta).time()


def format_hhmm(value):
    if isinstance(value, str):
        return value[:5]
    return value.strftime("%H:%M")


def assert_bookable_date(slot_date, now=None):
    today = cairo_today(now)
    latest = today + timedelta(days=settings.BOOKING_WINDOW_DAYS)
    if slot_date < today or slot_date > latest:
        errors.date_out_of_range()


def _parse_date(value):
    if hasattr(value, "year"):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        errors.invalid_slot("date must be YYYY-MM-DD.")


def _parse_start_time(value):
    if isinstance(value, time):
        return value.replace(second=0, microsecond=0)
    if isinstance(value, str):
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).time().replace(second=0, microsecond=0)
            except ValueError:
                continue
    errors.invalid_slot("start_time must be HH:MM.")


def _slot_datetime(slot_date, start, now=None):
    combined = datetime.combine(slot_date, start)
    return timezone.make_aware(combined, timezone.get_current_timezone())


def normalize_hold_slots(slots, now=None):
    if not slots:
        errors.invalid_slot("Provide at least one slot.")

    parsed = []
    for item in slots:
        if not isinstance(item, dict):
            errors.invalid_slot("Each slot must be an object.")
        court_id = item.get("court_id")
        if court_id is None:
            errors.invalid_slot("Each slot needs a court_id.")
        parsed.append(
            {
                "court_id": str(court_id),
                "date": _parse_date(item.get("date")),
                "start_time": _parse_start_time(item.get("start_time")),
            }
        )

    court_ids = {row["court_id"] for row in parsed}
    dates = {row["date"] for row in parsed}
    if len(court_ids) != 1 or len(dates) != 1:
        errors.mixed_slots()

    starts = [row["start_time"] for row in parsed]
    if len(starts) != len(set(starts)):
        errors.duplicate_slots()

    court_id = parsed[0]["court_id"]
    slot_date = parsed[0]["date"]
    try:
        court = Court.objects.get(pk=court_id)
    except (Court.DoesNotExist, ValueError, DjangoValidationError, TypeError):
        errors.not_found("No court matches this id.")

    assert_bookable_date(slot_date, now=now)

    grid = set(start_time_grid())
    local_now = cairo_now(now)
    normalized = []
    for row in parsed:
        start = row["start_time"]
        if start not in grid:
            errors.invalid_slot("Start time must be on the hour between 08:00 and 21:00.")
        if _slot_datetime(slot_date, start, now) <= local_now:
            errors.past_slot()
        try:
            pricing = price_for_start_time(start)
        except ValueError:
            errors.invalid_slot("Start time is outside operating hours.")
        normalized.append(
            {
                "court": court,
                "date": slot_date,
                "start_time": start,
                "price_egp": pricing["price_egp"],
                "price_cents": pricing["price_cents"],
                "period": pricing["period"],
            }
        )

    normalized.sort(key=lambda row: row["start_time"])
    return normalized


def slot_totals(normalized_slots):
    price_egp = sum(row["price_egp"] for row in normalized_slots)
    price_cents = sum(row["price_cents"] for row in normalized_slots)
    return price_egp, price_cents


def assert_transition(booking, to_status):
    allowed = ALLOWED_TRANSITIONS.get(booking.status, set())
    if to_status not in allowed:
        errors.invalid_transition(booking.status, to_status)


def can_cancel(booking):
    return booking.status in {Booking.Status.HELD, Booking.Status.PENDING_PAYMENT}


def can_checkout(booking, now=None):
    if booking.status not in {Booking.Status.HELD, Booking.Status.PENDING_PAYMENT}:
        return False
    if booking.hold_expires_at is None:
        return True
    return booking.hold_expires_at > cairo_now(now)


def booking_slots_list(booking):
    if hasattr(booking, "_prefetched_objects_cache") and "slots" in booking._prefetched_objects_cache:
        slots = list(booking.slots.all())
    else:
        slots = list(booking.slots.select_related("court").all())
    slots.sort(key=lambda slot: (slot.date, slot.start_time))
    return slots


def first_last_slots(booking):
    slots = booking_slots_list(booking)
    if not slots:
        return None, None
    return slots[0], slots[-1]


def booking_slot_date(booking):
    first, _ = first_last_slots(booking)
    return first.date if first else None


def booking_sort_key(booking):
    first, _ = first_last_slots(booking)
    if first is None:
        return (datetime.max.date(), time.max)
    return (first.date, first.start_time)


def booking_last_slot_end(booking):
    _, last = first_last_slots(booking)
    if last is None:
        return None
    return _slot_datetime(last.date, end_time_for(last.start_time))


def as_cairo_date(value=None):
    if value is None:
        return cairo_today()
    if isinstance(value, datetime):
        return cairo_today(value)
    return value


def can_redeem(booking, today=None):
    today = as_cairo_date(today)
    if booking.status != Booking.Status.CONFIRMED:
        return False
    if booking.redeemed_at is not None:
        return False
    slot_date = booking_slot_date(booking)
    return slot_date is not None and slot_date == today


def generate_booking_code():
    body = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
    return f"{CODE_PREFIX}{body}"


def issued_booking_code(booking):
    if booking.status not in CODE_VISIBLE_STATUSES:
        return None
    return booking.booking_code


def qr_payload(code):
    if not code:
        return None
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/pass/{code}"


def pass_url(code):
    if not code:
        return None
    return f"/pass/{code}"


def partition_my_bookings(bookings, now=None, today=None):
    if now is None and today is not None:
        now = datetime.combine(as_cairo_date(today), time.max)
        now = timezone.make_aware(now, timezone.get_current_timezone())
    now = cairo_now(now)
    upcoming = []
    past = []
    for booking in bookings:
        if booking.status not in UPCOMING_STATUSES:
            past.append(booking)
            continue
        end_at = booking_last_slot_end(booking)
        if end_at is not None and end_at > now:
            upcoming.append(booking)
        else:
            past.append(booking)
    return upcoming, past
