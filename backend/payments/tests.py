from datetime import time, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import requests
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tokens import issue_tokens
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import cairo_today
from payments.client import PaymobClient

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
