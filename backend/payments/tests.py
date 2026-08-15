import hashlib
import hmac as hmaclib
from datetime import time, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import requests
from django.test import SimpleTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tokens import issue_tokens
from bookings.hold import create_hold
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import cairo_today
from payments.client import PaymobClient
from payments.hmac import concat_transaction_post_fields, paymob_str, verify_transaction_post_hmac

PAYMOB_SECRET = "sk_test_secret_do_not_leak"
PAYMOB_PUBLIC = "egy_pk_test_public"
PAYMOB_INTEGRATION_ID = 4569876

PAYMOB_SETTINGS = {
    "PAYMOB_SECRET_KEY": PAYMOB_SECRET,
    "PAYMOB_PUBLIC_KEY": PAYMOB_PUBLIC,
    "PAYMOB_INTEGRATION_ID_CARD": str(PAYMOB_INTEGRATION_ID),
    "PAYMOB_BASE_URL": "https://accept.paymob.com",
    "PAYMOB_CHECKOUT_BASE_URL": "https://eg.checkout.paymob.com",
    "PAYMOB_TIMEOUT_SECONDS": 15,
    "PUBLIC_API_URL": "https://api.example.test",
    "FRONTEND_URL": "https://app.example.test",
}


def _paymob_response(status_code=201, body=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = body or {
        "id": "pi_test_8f3a1c2e",
        "client_secret": "egy_csk_test_abc",
    }
    return response


@override_settings(**PAYMOB_SETTINGS)
class PaymobClientTests(APITestCase):
    def test_authorization_uses_token_prefix(self):
        client = PaymobClient()
        self.assertEqual(client.session.headers["Authorization"], f"Token {PAYMOB_SECRET}")
        self.assertNotIn("Bearer", client.session.headers["Authorization"])

    def test_checkout_url_uses_live_egypt_host_and_public_key(self):
        url = PaymobClient().checkout_url("egy_csk_test_abc")
        self.assertTrue(url.startswith("https://eg.checkout.paymob.com/?"))
        self.assertIn(f"publicKey={PAYMOB_PUBLIC}", url)
        self.assertIn("clientSecret=egy_csk_test_abc", url)
        self.assertNotIn(PAYMOB_SECRET, url)


@override_settings(**PAYMOB_SETTINGS)
class CheckoutApiTests(APITestCase):
    def setUp(self):
        self.court = Court.objects.get(slug="court-1")
        self.slot_date = cairo_today() + timedelta(days=5)
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        self.other = User.objects.create_user(
            phone="01098765432",
            name="Omar Ali",
            password="secret12",
        )
        self._auth(self.user)

    def _auth(self, user):
        tokens = issue_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def _booking(self, **overrides):
        payload = {
            "user": self.user,
            "status": Booking.Status.HELD,
            "booker_name": self.user.name,
            "attendee_names": ["Ahmed Hassan", "Omar Ali"],
            "total_price_egp": 700,
            "total_price_cents": 70000,
            "hold_expires_at": timezone.now() + timedelta(minutes=10),
        }
        payload.update(overrides)
        return Booking.objects.create(**payload)

    def _slot(self, booking, start=time(18, 0), **overrides):
        payload = {
            "booking": booking,
            "court": self.court,
            "date": self.slot_date,
            "start_time": start,
            "price_egp": 350,
            "price_cents": 35000,
        }
        payload.update(overrides)
        return BookingSlot.objects.create(**payload)

    def _held_booking(self, **overrides):
        booking = self._booking(**overrides)
        self._slot(booking, time(18, 0))
        self._slot(booking, time(19, 0))
        return booking

    def _checkout(self, booking, query=""):
        url = f"/api/v1/bookings/{booking.id}/checkout"
        if query:
            url = f"{url}?{query}"
        return self.client.post(url, {}, format="json")

    def _assert_still_held(self, booking, hold_expires_at):
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.HELD)
        self.assertIsNone(booking.paymob_intention_id)
        self.assertEqual(booking.hold_expires_at, hold_expires_at)

    @patch("payments.client.requests.Session.post")
    def test_outgoing_payload_and_success_url(self, mock_post):
        mock_post.return_value = _paymob_response()
        booking = self._held_booking()

        response = self._checkout(booking)
        self.assertEqual(response.status_code, 200)
        body = response.json()

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://accept.paymob.com/v1/intention/")
        self.assertEqual(kwargs["timeout"], 15)
        payload = kwargs["json"]
        self.assertEqual(payload["amount"], 70000)
        self.assertEqual(payload["currency"], "EGP")
        self.assertEqual(payload["payment_methods"], [PAYMOB_INTEGRATION_ID])
        self.assertEqual(payload["special_reference"], str(booking.id))
        self.assertEqual(
            payload["notification_url"],
            "https://api.example.test/api/v1/webhooks/paymob",
        )
        self.assertEqual(
            payload["redirection_url"],
            f"https://app.example.test/book/pending?bookingId={booking.id}",
        )
        self.assertEqual(
            payload["items"],
            [
                {"name": "Court 1 18:00", "amount": 35000, "quantity": 1},
                {"name": "Court 1 19:00", "amount": 35000, "quantity": 1},
            ],
        )
        self.assertEqual(payload["billing_data"]["first_name"], "Ahmed")
        self.assertEqual(payload["billing_data"]["last_name"], "Hassan")
        self.assertEqual(payload["billing_data"]["phone_number"], "+201012345678")
        self.assertEqual(
            payload["billing_data"]["email"],
            "01012345678@customers.mahgooz.app",
        )
        self.assertEqual(payload["billing_data"]["country"], "EGY")
        self.assertGreaterEqual(payload["expiration"], 60)

        self.assertEqual(body["booking_id"], str(booking.id))
        self.assertEqual(body["status"], Booking.Status.PENDING_PAYMENT)
        self.assertEqual(body["amount_egp"], 700)
        self.assertEqual(body["amount_cents"], 70000)
        self.assertEqual(body["currency"], "EGP")
        self.assertEqual(body["paymob_intention_id"], "pi_test_8f3a1c2e")
        checkout_url = body["checkout_url"]
        self.assertTrue(checkout_url.startswith("https://eg.checkout.paymob.com/?"))
        self.assertIn(f"publicKey={PAYMOB_PUBLIC}", checkout_url)
        self.assertIn("clientSecret=egy_csk_test_abc", checkout_url)
        self.assertNotIn(PAYMOB_SECRET, checkout_url)
        self.assertNotIn(PAYMOB_SECRET, str(body))

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING_PAYMENT)
        self.assertEqual(booking.paymob_intention_id, "pi_test_8f3a1c2e")

    @patch("payments.client.requests.Session.post")
    def test_redirect_query_params_are_not_payment_confirmation(self, mock_post):
        mock_post.return_value = _paymob_response()
        booking = self._held_booking()
        response = self._checkout(
            booking,
            query="success=true&hmac=forged&id=289187034",
        )
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING_PAYMENT)
        self.assertNotEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertIsNone(booking.booking_code)

    @patch("payments.client.requests.Session.post")
    def test_paymob_http_error_keeps_held(self, mock_post):
        mock_post.return_value = _paymob_response(400, {"detail": "bad request"})
        booking = self._held_booking()
        expires = booking.hold_expires_at
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"]["code"], "PAYMOB_ERROR")
        self._assert_still_held(booking, expires)
        mock_post.assert_called_once()

    @patch("payments.client.requests.Session.post")
    def test_paymob_server_error_keeps_held(self, mock_post):
        mock_post.return_value = _paymob_response(500, {"detail": "upstream"})
        booking = self._held_booking()
        expires = booking.hold_expires_at
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 502)
        self._assert_still_held(booking, expires)
        mock_post.assert_called_once()

    @patch("payments.client.requests.Session.post")
    def test_paymob_timeout_keeps_held_and_does_not_retry(self, mock_post):
        mock_post.side_effect = requests.Timeout("timed out")
        booking = self._held_booking()
        expires = booking.hold_expires_at
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"]["code"], "PAYMOB_ERROR")
        self._assert_still_held(booking, expires)
        mock_post.assert_called_once()

    @patch("payments.client.requests.Session.post")
    def test_paymob_connect_timeout_keeps_held(self, mock_post):
        mock_post.side_effect = requests.ConnectTimeout("connect timed out")
        booking = self._held_booking()
        expires = booking.hold_expires_at
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 502)
        self._assert_still_held(booking, expires)
        mock_post.assert_called_once()

    @patch("payments.client.requests.Session.post")
    def test_unauthenticated(self, mock_post):
        booking = self._held_booking()
        self.client.credentials()
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 401)
        mock_post.assert_not_called()

    @patch("payments.client.requests.Session.post")
    def test_other_user_forbidden(self, mock_post):
        booking = self._held_booking()
        self._auth(self.other)
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.HELD)
        mock_post.assert_not_called()

    @patch("payments.client.requests.Session.post")
    def test_unknown_booking_not_found(self, mock_post):
        response = self.client.post(
            f"/api/v1/bookings/{uuid4()}/checkout",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        mock_post.assert_not_called()

    @patch("payments.client.requests.Session.post")
    def test_expired_hold(self, mock_post):
        booking = self._held_booking(
            hold_expires_at=timezone.now() - timedelta(minutes=1),
        )
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "HOLD_EXPIRED")
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        mock_post.assert_not_called()

    @patch("payments.client.requests.Session.post")
    def test_already_paid(self, mock_post):
        booking = self._held_booking(status=Booking.Status.CONFIRMED)
        response = self._checkout(booking)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "ALREADY_PAID")
        mock_post.assert_not_called()

    @patch("payments.client.requests.Session.post")
    def test_retry_pending_payment_creates_new_intention(self, mock_post):
        mock_post.side_effect = [
            _paymob_response(
                body={"id": "pi_test_first", "client_secret": "egy_csk_test_first"}
            ),
            _paymob_response(
                body={"id": "pi_test_second", "client_secret": "egy_csk_test_second"}
            ),
        ]
        booking = self._held_booking()
        first = self._checkout(booking)
        self.assertEqual(first.status_code, 200)
        second = self._checkout(booking)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["paymob_intention_id"], "pi_test_second")
        self.assertIn("clientSecret=egy_csk_test_second", second.json()["checkout_url"])
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.PENDING_PAYMENT)
        self.assertEqual(booking.paymob_intention_id, "pi_test_second")
        self.assertEqual(mock_post.call_count, 2)

    @patch("payments.client.requests.Session.post")
    def test_missing_config_does_not_call_paymob(self, mock_post):
        booking = self._held_booking()
        expires = booking.hold_expires_at
        with override_settings(PAYMOB_SECRET_KEY="", PAYMOB_PUBLIC_KEY=""):
            response = self._checkout(booking)
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"]["code"], "PAYMOB_ERROR")
        self._assert_still_held(booking, expires)
        mock_post.assert_not_called()


PAYMOB_HMAC_SECRET = "test_hmac_secret_do_not_leak"
WEBHOOK_SETTINGS = {
    **PAYMOB_SETTINGS,
    "PAYMOB_HMAC_SECRET": PAYMOB_HMAC_SECRET,
}

# Live Paymob POST HMAC sample (docs 2026-06-01).
PAYMOB_DOCS_OBJ = {
    "amount_cents": 100000,
    "created_at": "2024-06-13T11:33:44.592345",
    "currency": "EGP",
    "error_occured": False,
    "has_parent_transaction": False,
    "id": 19203646,
    "integration_id": 54097558,
    "is_3d_secure": True,
    "is_auth": False,
    "is_capture": False,
    "is_refunded": False,
    "is_standalone_payment": True,
    "is_voided": False,
    "order": {"id": 21750375},
    "owner": 4302852,
    "pending": False,
    "source_data": {"pan": "2346", "sub_type": "MasterCard", "type": "card"},
    "success": True,
}
PAYMOB_DOCS_CONCAT = (
    "1000002024-06-13T11:33:44.592345EGPfalsefalse1920364654097558"
    "truefalsefalsefalsetruefalse217503754302852false2346MasterCardcardtrue"
)


class PaymobHmacTests(SimpleTestCase):
    def test_docs_sample_concatenation(self):
        self.assertEqual(concat_transaction_post_fields(PAYMOB_DOCS_OBJ), PAYMOB_DOCS_CONCAT)

    def test_booleans_are_json_lowercase(self):
        self.assertEqual(paymob_str(True), "true")
        self.assertEqual(paymob_str(False), "false")
        self.assertNotEqual(paymob_str(True), "True")

    def test_verify_accepts_matching_sha512(self):
        digest = hmaclib.new(
            PAYMOB_HMAC_SECRET.encode(),
            PAYMOB_DOCS_CONCAT.encode(),
            hashlib.sha512,
        ).hexdigest()
        self.assertTrue(
            verify_transaction_post_hmac(
                PAYMOB_DOCS_OBJ,
                digest,
                secret=PAYMOB_HMAC_SECRET,
            )
        )

    def test_verify_rejects_forged_and_missing_fields(self):
        self.assertFalse(
            verify_transaction_post_hmac(
                PAYMOB_DOCS_OBJ,
                "deadbeef",
                secret=PAYMOB_HMAC_SECRET,
            )
        )
        incomplete = dict(PAYMOB_DOCS_OBJ)
        del incomplete["source_data"]
        digest = hmaclib.new(
            PAYMOB_HMAC_SECRET.encode(),
            PAYMOB_DOCS_CONCAT.encode(),
            hashlib.sha512,
        ).hexdigest()
        self.assertFalse(
            verify_transaction_post_hmac(
                incomplete,
                digest,
                secret=PAYMOB_HMAC_SECRET,
            )
        )


@override_settings(**WEBHOOK_SETTINGS)
class PaymobWebhookApiTests(APITestCase):
    def setUp(self):
        self.court = Court.objects.get(slug="court-1")
        self.slot_date = cairo_today() + timedelta(days=5)
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        self.other = User.objects.create_user(
            phone="01098765432",
            name="Omar Ali",
            password="secret12",
        )

    def _booking(self, **overrides):
        payload = {
            "user": self.user,
            "status": Booking.Status.PENDING_PAYMENT,
            "booker_name": self.user.name,
            "attendee_names": ["Ahmed Hassan", "Omar Ali"],
            "total_price_egp": 700,
            "total_price_cents": 70000,
            "hold_expires_at": timezone.now() + timedelta(minutes=10),
        }
        payload.update(overrides)
        return Booking.objects.create(**payload)

    def _slot(self, booking, start=time(18, 0), **overrides):
        payload = {
            "booking": booking,
            "court": self.court,
            "date": self.slot_date,
            "start_time": start,
            "price_egp": 350,
            "price_cents": 35000,
        }
        payload.update(overrides)
        return BookingSlot.objects.create(**payload)

    def _unpaid_booking(self, **overrides):
        booking = self._booking(**overrides)
        self._slot(booking, time(18, 0))
        self._slot(booking, time(19, 0))
        return booking

    def _obj(self, booking, **overrides):
        obj = {
            "amount_cents": booking.total_price_cents,
            "created_at": "2026-08-15T13:24:11.123456",
            "currency": "EGP",
            "error_occured": False,
            "has_parent_transaction": False,
            "id": 289187034,
            "integration_id": 123456,
            "is_3d_secure": True,
            "is_auth": False,
            "is_capture": False,
            "is_refunded": False,
            "is_standalone_payment": True,
            "is_voided": False,
            "order": {
                "id": 998877,
                "merchant_order_id": str(booking.id),
            },
            "owner": 111222,
            "pending": False,
            "source_data": {
                "pan": "2346",
                "sub_type": "MasterCard",
                "type": "card",
            },
            "success": True,
        }
        obj.update(overrides)
        if "order" in overrides and isinstance(overrides["order"], dict):
            order = {
                "id": 998877,
                "merchant_order_id": str(booking.id),
            }
            order.update(overrides["order"])
            obj["order"] = order
        return obj

    def _sign(self, obj):
        concat = concat_transaction_post_fields(obj)
        return hmaclib.new(
            PAYMOB_HMAC_SECRET.encode(),
            concat.encode(),
            hashlib.sha512,
        ).hexdigest()

    def _post(self, obj, hmac_value=None, body=None, query=True):
        payload = body if body is not None else {"type": "TRANSACTION", "obj": obj}
        if hmac_value is None and obj is not None:
            hmac_value = self._sign(obj)
        url = "/api/v1/webhooks/paymob"
        if query and hmac_value:
            url = f"{url}?hmac={hmac_value}"
        elif not query and hmac_value is not None:
            payload = dict(payload)
            payload["hmac"] = hmac_value
        return self.client.post(url, payload, format="json")

    def _assert_unpaid_held(self, booking, status=Booking.Status.PENDING_PAYMENT):
        booking.refresh_from_db()
        self.assertEqual(booking.status, status)
        self.assertIsNone(booking.booking_code)
        self.assertEqual(booking.slots.filter(released_at__isnull=True).count(), 2)

    def test_forged_hmac_does_not_change_booking(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking)
        response = self._post(obj, hmac_value="deadbeef" * 16)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "INVALID_HMAC")
        self._assert_unpaid_held(booking)
        self.assertIsNone(booking.paymob_transaction_id)

    def test_malformed_empty_body(self):
        booking = self._unpaid_booking()
        response = self.client.post("/api/v1/webhooks/paymob", {}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "INVALID_HMAC")
        self._assert_unpaid_held(booking)

    def test_malformed_missing_obj(self):
        booking = self._unpaid_booking()
        response = self.client.post(
            "/api/v1/webhooks/paymob?hmac=abc",
            {"type": "TRANSACTION"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)
        self._assert_unpaid_held(booking)

    def test_malformed_missing_hmac_fields(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking)
        del obj["source_data"]
        concat = (
            "700002026-08-15T13:24:11.123456EGPfalsefalse289187034123456"
            "truefalsefalsefalsetruefalse998877111222false"
        )
        digest = hmaclib.new(
            PAYMOB_HMAC_SECRET.encode(),
            concat.encode(),
            hashlib.sha512,
        ).hexdigest()
        response = self._post(obj, hmac_value=digest)
        self.assertEqual(response.status_code, 401)
        self._assert_unpaid_held(booking)

    def test_malformed_invalid_json(self):
        response = self.client.post(
            "/api/v1/webhooks/paymob?hmac=abc",
            data="{not-json",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "INVALID_HMAC")

    def test_successful_confirms_and_issues_code(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking)
        response = self._post(obj)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["received"])
        self.assertEqual(body["booking_id"], str(booking.id))
        self.assertEqual(body["status"], Booking.Status.CONFIRMED)
        self.assertRegex(body["booking_code"], r"^MGZ-[A-Z0-9]{5}$")
        self.assertNotIn("idempotent", body)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.paymob_transaction_id, "289187034")
        self.assertEqual(booking.booking_code, body["booking_code"])
        self.assertEqual(booking.slots.filter(released_at__isnull=True).count(), 2)

    def test_hmac_query_param_is_used_not_body(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking)
        good = self._sign(obj)
        response = self.client.post(
            f"/api/v1/webhooks/paymob?hmac={good}",
            {"type": "TRANSACTION", "obj": obj, "hmac": "forged-in-body"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_hmac_in_body_accepted_when_query_missing(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking)
        response = self._post(obj, query=False)
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)

    def test_failed_releases_slots(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking, success=False, error_occured=True, id=289187099)
        response = self._post(obj)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], Booking.Status.FAILED)
        self.assertIsNone(body["booking_code"])

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.FAILED)
        self.assertEqual(booking.paymob_transaction_id, "289187099")
        self.assertEqual(booking.slots.filter(released_at__isnull=True).count(), 0)
        self.assertEqual(booking.slots.filter(released_at__isnull=False).count(), 2)

        reheld = create_hold(
            user=self.other,
            slots=[
                {
                    "court_id": str(self.court.id),
                    "date": self.slot_date.isoformat(),
                    "start_time": "18:00",
                }
            ],
            attendee_names=["Omar Ali"],
        )
        self.assertEqual(reheld.status, Booking.Status.HELD)

    def test_duplicate_success_is_idempotent(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking)
        first = self._post(obj)
        self.assertEqual(first.status_code, 200)
        code = first.json()["booking_code"]
        second = self._post(obj)
        self.assertEqual(second.status_code, 200)
        body = second.json()
        self.assertTrue(body["idempotent"])
        self.assertEqual(body["booking_code"], code)
        self.assertEqual(body["status"], Booking.Status.CONFIRMED)
        self.assertEqual(Booking.objects.filter(booking_code=code).count(), 1)
        booking.refresh_from_db()
        self.assertEqual(booking.booking_code, code)
        self.assertEqual(booking.paymob_transaction_id, "289187034")

    def test_mismatched_booking_unknown_uuid(self):
        booking = self._unpaid_booking()
        unknown = uuid4()
        obj = self._obj(booking, order={"merchant_order_id": str(unknown)})
        response = self._post(obj)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self._assert_unpaid_held(booking)
        self.assertFalse(Booking.objects.filter(pk=unknown).exists())

    def test_late_success_does_not_displace_newer_hold(self):
        now = timezone.now()
        expired = self._booking(status=Booking.Status.EXPIRED)
        self._slot(expired, time(18, 0), released_at=now)
        self._slot(expired, time(19, 0), released_at=now)
        newer = self._booking(user=self.other, status=Booking.Status.HELD)
        self._slot(newer, time(18, 0))
        self._slot(newer, time(19, 0))

        obj = self._obj(expired, id=555000111)
        with self.assertLogs("payments.webhook", level="WARNING") as logs:
            response = self._post(obj)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any("MANUAL_PAYMENT_EXCEPTION" in line for line in logs.output))

        expired.refresh_from_db()
        newer.refresh_from_db()
        self.assertEqual(expired.status, Booking.Status.EXPIRED)
        self.assertIsNone(expired.booking_code)
        self.assertEqual(expired.paymob_transaction_id, "555000111")
        self.assertEqual(newer.status, Booking.Status.HELD)
        self.assertIsNone(newer.booking_code)
        self.assertEqual(newer.slots.filter(released_at__isnull=True).count(), 2)
        self.assertEqual(expired.slots.filter(released_at__isnull=True).count(), 0)

    def test_pending_callback_is_noop(self):
        booking = self._unpaid_booking()
        obj = self._obj(booking, pending=True, success=False)
        response = self._post(obj)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"received": True})
        self._assert_unpaid_held(booking)
        self.assertIsNone(booking.paymob_transaction_id)

    def test_fail_after_confirmed_is_ignored(self):
        booking = self._unpaid_booking()
        success_obj = self._obj(booking)
        self.assertEqual(self._post(success_obj).status_code, 200)
        booking.refresh_from_db()
        code = booking.booking_code
        fail_obj = self._obj(booking, success=False, error_occured=True, id=289187999)
        response = self._post(fail_obj)
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertEqual(booking.booking_code, code)
        self.assertEqual(booking.paymob_transaction_id, "289187034")
        self.assertEqual(booking.slots.filter(released_at__isnull=True).count(), 2)

    def test_unauthenticated_webhook_does_not_need_jwt(self):
        booking = self._unpaid_booking()
        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")
        response = self._post(self._obj(booking))
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
