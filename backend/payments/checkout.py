from django.conf import settings
from django.db import transaction

from bookings import errors
from bookings.expiry import expire_elapsed_holds
from bookings.models import Booking
from bookings.policies import assert_transition, cairo_now, can_checkout, format_hhmm
from payments.client import PaymobClient, PaymobClientError

CURRENCY = "EGP"
PLACEHOLDER_ADDRESS = "NA"
MIN_INTENTION_EXPIRATION_SECONDS = 60
PAID_STATUSES = {Booking.Status.CONFIRMED, Booking.Status.REDEEMED}


def start_checkout(*, user, booking_id, now=None, client=None):
    now = cairo_now(now)
    expire_elapsed_holds(now=now)
    with transaction.atomic():
        try:
            booking = (
                Booking.objects.select_for_update()
                .select_related("user")
                .prefetch_related("slots__court")
                .get(pk=booking_id)
            )
        except Booking.DoesNotExist:
            errors.not_found("Booking not found.")
        _assert_checkout_allowed(booking, user=user, now=now)
        paymob = client or PaymobClient()
        if not paymob.is_configured():
            errors.paymob_error()
        payload = build_intention_payload(
            booking,
            now=now,
            integration_id=paymob.card_integration_id(),
        )
        try:
            intention = paymob.create_intention(payload)
        except PaymobClientError:
            errors.paymob_error()
        if booking.status != Booking.Status.PENDING_PAYMENT:
            assert_transition(booking, Booking.Status.PENDING_PAYMENT)
            booking.status = Booking.Status.PENDING_PAYMENT
        booking.paymob_intention_id = intention["id"]
        booking.save(update_fields=["status", "paymob_intention_id", "updated_at"])
        return {
            "booking_id": str(booking.id),
            "status": booking.status,
            "amount_egp": booking.total_price_egp,
            "amount_cents": booking.total_price_cents,
            "currency": CURRENCY,
            "checkout_url": paymob.checkout_url(intention["client_secret"]),
            "paymob_intention_id": intention["id"],
        }


def _assert_checkout_allowed(booking, *, user, now):
    if booking.user_id != user.id:
        errors.forbidden("You do not own this booking.")
    if booking.status in PAID_STATUSES:
        errors.already_paid()
    if booking.status == Booking.Status.EXPIRED:
        errors.hold_expired()
    if not can_checkout(booking, now=now):
        if booking.hold_expires_at is not None and booking.hold_expires_at <= now:
            errors.hold_expired()
        errors.invalid_transition(booking.status, Booking.Status.PENDING_PAYMENT)


def build_intention_payload(booking, *, now, integration_id):
    slots = [
        slot
        for slot in booking.slots.all()
        if slot.released_at is None
    ]
    slots.sort(key=lambda slot: (slot.date, slot.start_time))
    slot_cents = sum(slot.price_cents for slot in slots)
    if slot_cents != booking.total_price_cents:
        errors.internal_error()

    items = [
        {
            "name": _item_name(slot),
            "amount": slot.price_cents,
            "quantity": 1,
        }
        for slot in slots
    ]
    first_name, last_name = _split_name(booking.booker_name)
    owner = booking.user
    return {
        "amount": booking.total_price_cents,
        "currency": CURRENCY,
        "payment_methods": [integration_id],
        "items": items,
        "billing_data": {
            "first_name": first_name,
            "last_name": last_name,
            "email": _billing_email(owner),
            "phone_number": _paymob_phone(owner.phone),
            "apartment": PLACEHOLDER_ADDRESS,
            "floor": PLACEHOLDER_ADDRESS,
            "street": PLACEHOLDER_ADDRESS,
            "building": PLACEHOLDER_ADDRESS,
            "city": PLACEHOLDER_ADDRESS,
            "state": PLACEHOLDER_ADDRESS,
            "country": "EGY",
        },
        "special_reference": str(booking.id),
        "expiration": _remaining_expiration(booking, now),
        "notification_url": f"{settings.PUBLIC_API_URL}/api/v1/webhooks/paymob",
        "redirection_url": (
            f"{settings.FRONTEND_URL}/book/pending?bookingId={booking.id}"
        ),
    }


def _item_name(slot):
    return f"{slot.court.name} {format_hhmm(slot.start_time)}"[:50]


def _split_name(name):
    parts = (name or "").strip().split()
    if not parts:
        return "NA", "NA"
    first = parts[0][:50]
    last = " ".join(parts[1:])[:50] if len(parts) > 1 else "NA"
    return first, last


def _paymob_phone(phone):
    digits = (phone or "").strip()
    if digits.startswith("01") and len(digits) == 11:
        return f"+20{digits[1:]}"
    return digits


def _billing_email(user):
    if user.email:
        return user.email
    return f"{user.phone}@customers.mahgooz.app"


def _remaining_expiration(booking, now):
    if booking.hold_expires_at is None:
        return max(int(settings.HOLD_TTL.total_seconds()), MIN_INTENTION_EXPIRATION_SECONDS)
    remaining = int((booking.hold_expires_at - now).total_seconds())
    return max(remaining, MIN_INTENTION_EXPIRATION_SECONDS)
