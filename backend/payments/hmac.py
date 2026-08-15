"""Paymob Transaction Processed (POST) HMAC-SHA512 verification.

Field order is the live Paymob POST callback list (docs last updated 2026-06-01):
https://developers.paymob.com/paymob-docs/webhook-callbacks-and-hmac/hmac/hmac-transaction-callback.md
"""

import hashlib
import hmac

from django.conf import settings

# Concatenation order is Paymob's documented POST list — not a re-sort of key names.
POST_HMAC_FIELDS = (
    "amount_cents",
    "created_at",
    "currency",
    "error_occured",
    "has_parent_transaction",
    "id",
    "integration_id",
    "is_3d_secure",
    "is_auth",
    "is_capture",
    "is_refunded",
    "is_standalone_payment",
    "is_voided",
    "order.id",
    "owner",
    "pending",
    "source_data.pan",
    "source_data.sub_type",
    "source_data.type",
    "success",
)


class HmacFieldError(LookupError):
    """A required HMAC field is missing from the raw callback obj."""


def paymob_str(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return str(value)


def _raw_field(obj, path):
    current = obj
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise HmacFieldError(path)
        current = current[part]
    return current


def concat_transaction_post_fields(obj):
    """Concatenate raw callback values in Paymob's POST HMAC order."""
    if not isinstance(obj, dict):
        raise HmacFieldError("obj")
    return "".join(paymob_str(_raw_field(obj, path)) for path in POST_HMAC_FIELDS)


def compute_transaction_post_hmac(obj, secret=None):
    secret = (secret if secret is not None else settings.PAYMOB_HMAC_SECRET) or ""
    concat = concat_transaction_post_fields(obj)
    return hmac.new(secret.encode(), concat.encode(), hashlib.sha512).hexdigest()


def verify_transaction_post_hmac(obj, received_hmac, secret=None):
    received = (received_hmac or "").strip().lower()
    secret = (secret if secret is not None else settings.PAYMOB_HMAC_SECRET) or ""
    if not received or not secret:
        return False
    try:
        computed = compute_transaction_post_hmac(obj, secret=secret)
    except HmacFieldError:
        return False
    return hmac.compare_digest(computed, received)
