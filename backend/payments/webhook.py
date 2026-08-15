"""HMAC-first Paymob webhook: correlate by special_reference, then apply state."""

import logging
from uuid import UUID

from django.db import IntegrityError, transaction

from bookings import errors
from bookings.models import Booking, BookingSlot
from bookings.policies import assert_transition, cairo_now, generate_booking_code
from payments.hmac import verify_transaction_post_hmac

logger = logging.getLogger("payments.webhook")

UNPAID_STATUSES = {Booking.Status.HELD, Booking.Status.PENDING_PAYMENT}
PAID_STATUSES = {Booking.Status.CONFIRMED, Booking.Status.REDEEMED}
CODE_ATTEMPTS = 8
MANUAL_PAYMENT_EXCEPTION = "MANUAL_PAYMENT_EXCEPTION"


def process_paymob_callback(*, body, received_hmac):
    obj = _untrusted_obj(body)
    if not verify_transaction_post_hmac(obj, received_hmac):
        errors.invalid_hmac()

    if _is_true(obj.get("pending")):
        return {"received": True}

    txn_id = str(obj.get("id", "")).strip()
    if not txn_id:
        errors.invalid_hmac()

    booking_id = _booking_id(obj)
    success = _is_true(obj.get("success"))

    try:
        with transaction.atomic():
            return _apply_locked(booking_id, txn_id, success)
    except IntegrityError:
        logger.warning(
            "Paymob callback IntegrityError for txn=%s booking=%s; treated as no-op",
            txn_id,
            booking_id,
        )
        return {"received": True}


def _untrusted_obj(body):
    if not isinstance(body, dict):
        errors.invalid_hmac()
    obj = body.get("obj")
    if not isinstance(obj, dict):
        errors.invalid_hmac()
    return obj


def _booking_id(obj):
    order = obj.get("order")
    if not isinstance(order, dict):
        errors.not_found("No booking matches this payment reference.")
    raw = order.get("merchant_order_id")
    try:
        return UUID(str(raw))
    except (TypeError, ValueError, AttributeError):
        errors.not_found("No booking matches this payment reference.")


def _apply_locked(booking_id, txn_id, success):
    try:
        booking = (
            Booking.objects.select_for_update()
            .prefetch_related("slots")
            .get(pk=booking_id)
        )
    except Booking.DoesNotExist:
        errors.not_found("No booking matches this payment reference.")

    if Booking.objects.filter(paymob_transaction_id=txn_id).exclude(pk=booking.pk).exists():
        logger.warning(
            "Paymob txn %s already belongs to another booking; ignored for %s",
            txn_id,
            booking.id,
        )
        return _received(booking)

    if booking.paymob_transaction_id == txn_id:
        return _received(booking, idempotent=True)

    if success:
        return _handle_success(booking, txn_id)
    return _handle_failure(booking, txn_id)


def _handle_success(booking, txn_id):
    if booking.status in PAID_STATUSES:
        _try_store_txn(booking, txn_id)
        return _received(booking, idempotent=True)

    if booking.status in UNPAID_STATUSES and _slots_still_held(booking):
        return _confirm(booking, txn_id)

    _log_manual_exception(booking, txn_id)
    _try_store_txn(booking, txn_id)
    return _received(booking)


def _handle_failure(booking, txn_id):
    if booking.status in PAID_STATUSES:
        return _received(booking)

    if booking.status in UNPAID_STATUSES:
        return _fail(booking, txn_id)

    _try_store_txn(booking, txn_id)
    return _received(booking)


def _confirm(booking, txn_id):
    assert_transition(booking, Booking.Status.CONFIRMED)
    booking.status = Booking.Status.CONFIRMED
    booking.paymob_transaction_id = txn_id
    _issue_booking_code(booking)
    return _received(booking)


def _fail(booking, txn_id):
    now = cairo_now()
    assert_transition(booking, Booking.Status.FAILED)
    booking.status = Booking.Status.FAILED
    booking.paymob_transaction_id = txn_id
    booking.save(update_fields=["status", "paymob_transaction_id", "updated_at"])
    booking.slots.filter(released_at__isnull=True).update(released_at=now)
    return _received(booking)


def _issue_booking_code(booking):
    if booking.booking_code:
        booking.save(update_fields=["status", "paymob_transaction_id", "updated_at"])
        return
    last_error = None
    for _ in range(CODE_ATTEMPTS):
        booking.booking_code = generate_booking_code()
        try:
            with transaction.atomic():
                booking.save(
                    update_fields=[
                        "status",
                        "paymob_transaction_id",
                        "booking_code",
                        "updated_at",
                    ]
                )
            return
        except IntegrityError as exc:
            last_error = exc
            if _is_booking_code_conflict(exc):
                continue
            raise
    logger.exception("Could not issue unique booking code", exc_info=last_error)
    errors.internal_error()


def _try_store_txn(booking, txn_id):
    if booking.paymob_transaction_id:
        return
    if Booking.objects.filter(paymob_transaction_id=txn_id).exists():
        return
    booking.paymob_transaction_id = txn_id
    booking.save(update_fields=["paymob_transaction_id", "updated_at"])


def _slots_still_held(booking):
    slots = list(booking.slots.all())
    return bool(slots) and all(slot.released_at is None for slot in slots)


def _log_manual_exception(booking, txn_id):
    displaced = _other_active_slot_exists(booking)
    logger.warning(
        "%s booking_id=%s paymob_transaction_id=%s status=%s slot_held_by_other=%s",
        MANUAL_PAYMENT_EXCEPTION,
        booking.id,
        txn_id,
        booking.status,
        displaced,
    )


def _other_active_slot_exists(booking):
    for slot in booking.slots.all():
        taken = (
            BookingSlot.objects.filter(
                court_id=slot.court_id,
                date=slot.date,
                start_time=slot.start_time,
                released_at__isnull=True,
            )
            .exclude(booking_id=booking.id)
            .exists()
        )
        if taken:
            return True
    return False


def _received(booking, *, idempotent=False):
    payload = {
        "received": True,
        "booking_id": str(booking.id),
        "status": booking.status,
        "booking_code": booking.booking_code,
    }
    if idempotent:
        payload["idempotent"] = True
    return payload


def _is_true(value):
    if value is True:
        return True
    if isinstance(value, str) and value.lower() == "true":
        return True
    return False


def _is_booking_code_conflict(exc):
    cause = getattr(exc, "__cause__", None)
    diag = getattr(cause, "diag", None)
    constraint = getattr(diag, "constraint_name", None) if diag is not None else None
    haystack = f"{constraint or ''} {exc}"
    return "booking_code" in haystack
