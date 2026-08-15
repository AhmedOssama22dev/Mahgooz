from rest_framework import status

from config.exceptions import APIError


def date_out_of_range(message=None):
    raise APIError(
        "DATE_OUT_OF_RANGE",
        message or "Date must be today or within the next 14 days.",
        status.HTTP_400_BAD_REQUEST,
    )


def past_slot(message=None):
    raise APIError(
        "PAST_SLOT",
        message or "Cannot book a slot that has already started.",
        status.HTTP_400_BAD_REQUEST,
    )


def invalid_slot(message=None):
    raise APIError(
        "INVALID_SLOT",
        message or "Invalid slot.",
        status.HTTP_400_BAD_REQUEST,
    )


def invalid_query(details, message=None):
    raise APIError(
        "VALIDATION_ERROR",
        message or "Invalid query parameters",
        status.HTTP_400_BAD_REQUEST,
        details=details,
    )


def mixed_slots(message=None):
    raise APIError(
        "MIXED_SLOTS",
        message or "All slots in a booking must share the same court and date.",
        status.HTTP_400_BAD_REQUEST,
    )


def duplicate_slots(message=None):
    raise APIError(
        "DUPLICATE_SLOTS",
        message or "Duplicate start times are not allowed in one booking.",
        status.HTTP_400_BAD_REQUEST,
    )


def slot_taken(conflicting_slots, message=None):
    raise APIError(
        "SLOT_TAKEN",
        message
        or "One or more slots were just booked. None of the requested slots were held.",
        status.HTTP_409_CONFLICT,
        details={"conflicting_slots": conflicting_slots},
    )


def cannot_cancel(message=None):
    raise APIError(
        "CANNOT_CANCEL",
        message or "This booking cannot be cancelled.",
        status.HTTP_409_CONFLICT,
    )


def hold_expired(message=None):
    raise APIError(
        "HOLD_EXPIRED",
        message or "Your hold expired. Please pick the slot again.",
        status.HTTP_409_CONFLICT,
    )


def already_paid(message=None):
    raise APIError(
        "ALREADY_PAID",
        message or "This booking is already confirmed.",
        status.HTTP_409_CONFLICT,
    )


def payment_not_confirmed(message=None):
    raise APIError(
        "PAYMENT_NOT_CONFIRMED",
        message or "Payment not confirmed yet.",
        status.HTTP_409_CONFLICT,
    )


def already_redeemed(message=None):
    raise APIError(
        "ALREADY_REDEEMED",
        message or "This pass was already redeemed.",
        status.HTTP_409_CONFLICT,
    )


def wrong_day(message=None):
    raise APIError(
        "WRONG_DAY",
        message or "This pass is not for today.",
        status.HTTP_409_CONFLICT,
    )


def invalid_transition(current, target):
    raise APIError(
        "INVALID_TRANSITION",
        f"Cannot change status from {current} to {target}.",
        status.HTTP_409_CONFLICT,
    )


def invalid_hmac(message=None):
    raise APIError(
        "INVALID_HMAC",
        message or "Callback HMAC verification failed.",
        status.HTTP_401_UNAUTHORIZED,
    )


def forbidden(message=None):
    raise APIError(
        "FORBIDDEN",
        message or "You do not have permission to perform this action.",
        status.HTTP_403_FORBIDDEN,
    )


def not_found(message=None):
    raise APIError(
        "NOT_FOUND",
        message or "Not found.",
        status.HTTP_404_NOT_FOUND,
    )


def not_implemented(message=None):
    raise APIError(
        "NOT_IMPLEMENTED",
        message or "Not implemented yet.",
        status.HTTP_501_NOT_IMPLEMENTED,
    )


def paymob_error(message=None):
    raise APIError(
        "PAYMOB_ERROR",
        message
        or "Could not start checkout. Your slot is still held — try again.",
        status.HTTP_502_BAD_GATEWAY,
    )


def internal_error(message=None):
    raise APIError(
        "INTERNAL_ERROR",
        message or "Unexpected server error",
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
