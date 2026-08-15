from datetime import time, timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tokens import issue_tokens
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import cairo_today
from bookings.seed import seed_courts

PUBLIC_PASS_KEYS = {
    "booking_code",
    "status",
    "court",
    "date",
    "start_times",
    "start_time",
    "end_time",
    "booker_name",
    "attendee_names",
    "price_egp",
    "qr_payload",
    "redeemed_at",
}

STATUS_KEYS = {"id", "status", "booking_code", "pass_url", "hold_expires_at"}


def collect_keys(obj):
    keys = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            keys.add(str(key))
            keys.update(collect_keys(value))
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            keys.update(collect_keys(item))
    return keys


def has_sensitive_key(obj):
    return any("phone" in key.lower() or "paymob" in key.lower() for key in collect_keys(obj))


class CustomerBookingPassApiTests(APITestCase):
    def setUp(self):
        seed_courts()
        self.court = Court.objects.get(slug="court-1")
        self.other_court = Court.objects.get(slug="court-2")
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

    def _clear_auth(self):
        self.client.credentials()

    def _booking(self, **overrides):
        payload = {
            "user": self.user,
            "status": Booking.Status.HELD,
            "booker_name": self.user.name,
            "attendee_names": ["Ahmed Hassan", "Omar Ali"],
            "total_price_egp": 350,
            "total_price_cents": 35000,
            "hold_expires_at": timezone.now() + timedelta(minutes=10),
        }
        payload.update(overrides)
        return Booking.objects.create(**payload)

    def _slot(self, booking, start=time(18, 0), court=None, date=None, **overrides):
        payload = {
            "booking": booking,
            "court": court or self.court,
            "date": date or self.slot_date,
            "start_time": start,
            "price_egp": 350,
            "price_cents": 35000,
        }
        payload.update(overrides)
        return BookingSlot.objects.create(**payload)

    def test_unauthenticated_status_list_and_detail_are_401(self):
        booking = self._booking()
        self._slot(booking)
        self._clear_auth()
        for url in (
            f"/api/v1/bookings/{booking.id}/status",
            "/api/v1/bookings",
            f"/api/v1/bookings/{booking.id}",
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 401, url)
            self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")

    def test_other_user_cannot_read_status_or_detail(self):
        booking = self._booking()
        self._slot(booking)
        self._auth(self.other)
        for url in (
            f"/api/v1/bookings/{booking.id}/status",
            f"/api/v1/bookings/{booking.id}",
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)
            error = response.json()["error"]
            self.assertEqual(error["code"], "FORBIDDEN")
            self.assertEqual(error["message"], "You do not own this booking.")

    def test_unknown_booking_is_not_found(self):
        missing = uuid4()
        for url in (
            f"/api/v1/bookings/{missing}/status",
            f"/api/v1/bookings/{missing}",
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, url)
            self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_list_never_includes_another_users_bookings(self):
        mine = self._booking(status=Booking.Status.CONFIRMED, booking_code="MGZ-7F42K")
        self._slot(mine)
        theirs = self._booking(
            user=self.other,
            status=Booking.Status.CONFIRMED,
            booker_name=self.other.name,
            booking_code="MGZ-2K91P",
        )
        self._slot(theirs, court=self.other_court)
        response = self.client.get("/api/v1/bookings")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        ids = {item["id"] for item in body["upcoming"] + body["past"]}
        self.assertEqual(ids, {str(mine.id)})
        self.assertNotIn(str(theirs.id), ids)

    def test_held_and_pending_status_hide_booking_code(self):
        held = self._booking(status=Booking.Status.HELD, booking_code="MGZ-HELD1")
        self._slot(held)
        pending = self._booking(
            status=Booking.Status.PENDING_PAYMENT,
            booking_code="MGZ-PEND1",
        )
        self._slot(pending, start=time(19, 0))

        held_status = self.client.get(f"/api/v1/bookings/{held.id}/status")
        self.assertEqual(held_status.status_code, 200)
        self.assertEqual(set(held_status.json().keys()), STATUS_KEYS)
        self.assertEqual(held_status.json()["status"], "held")
        self.assertIsNone(held_status.json()["booking_code"])
        self.assertIsNone(held_status.json()["pass_url"])

        held_detail = self.client.get(f"/api/v1/bookings/{held.id}")
        self.assertEqual(held_detail.status_code, 200)
        self.assertIsNone(held_detail.json()["booking_code"])
        self.assertIsNone(held_detail.json()["qr_payload"])
        self.assertFalse(has_sensitive_key(held_detail.json()))

        pending_status = self.client.get(f"/api/v1/bookings/{pending.id}/status")
        self.assertEqual(pending_status.json()["status"], "pending_payment")
        self.assertIsNone(pending_status.json()["booking_code"])

    def test_confirmed_status_returns_code_for_pending_redirect(self):
        booking = self._booking(status=Booking.Status.CONFIRMED, booking_code="MGZ-7F42K")
        self._slot(booking)
        response = self.client.get(f"/api/v1/bookings/{booking.id}/status")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body.keys()), STATUS_KEYS)
        self.assertEqual(body["status"], "confirmed")
        self.assertEqual(body["booking_code"], "MGZ-7F42K")
        self.assertEqual(body["pass_url"], "/pass/MGZ-7F42K")

        detail = self.client.get(f"/api/v1/bookings/{booking.id}").json()
        self.assertEqual(detail["court"]["name"], "Court 1")
        self.assertEqual(detail["start_time"], "18:00")
        self.assertEqual(detail["end_time"], "19:00")
        self.assertEqual(detail["booking_code"], "MGZ-7F42K")

    def test_expired_hold_surfaces_as_expired_on_poll(self):
        booking = self._booking(hold_expires_at=timezone.now() - timedelta(minutes=1))
        self._slot(booking)
        response = self.client.get(f"/api/v1/bookings/{booking.id}/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "expired")
        self.assertIsNone(response.json()["booking_code"])
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)

    def test_list_partitions_upcoming_and_past(self):
        upcoming = self._booking(status=Booking.Status.CONFIRMED, booking_code="MGZ-7F42K")
        self._slot(upcoming, date=self.slot_date, start=time(18, 0))
        later = self._booking(status=Booking.Status.CONFIRMED, booking_code="MGZ-8G53L")
        self._slot(later, date=self.slot_date + timedelta(days=1), start=time(9, 0))
        redeemed = self._booking(status=Booking.Status.REDEEMED, booking_code="MGZ-2K91P")
        self._slot(redeemed, date=cairo_today() - timedelta(days=2), start=time(19, 0))
        failed = self._booking(status=Booking.Status.FAILED)
        self._slot(failed, date=self.slot_date, start=time(20, 0))

        response = self.client.get("/api/v1/bookings")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(
            [item["id"] for item in body["upcoming"]],
            [str(upcoming.id), str(later.id)],
        )
        self.assertEqual(body["upcoming"][0]["booking_code"], "MGZ-7F42K")
        past_ids = [item["id"] for item in body["past"]]
        self.assertEqual(past_ids, [str(failed.id), str(redeemed.id)])
        self.assertIsNone(next(item["booking_code"] for item in body["past"] if item["id"] == str(failed.id)))

    def test_public_pass_confirmed_and_redeemed(self):
        confirmed = self._booking(
            status=Booking.Status.CONFIRMED,
            booking_code="MGZ-7F42K",
            paymob_intention_id="pi_secret",
            paymob_transaction_id="txn-289187034",
        )
        self._slot(confirmed)
        self._slot(confirmed, start=time(19, 0))
        self._clear_auth()

        response = self.client.get("/api/v1/passes/MGZ-7F42K")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body.keys()), PUBLIC_PASS_KEYS)
        self.assertFalse(has_sensitive_key(body))
        self.assertNotIn("id", body)
        self.assertEqual(body["booking_code"], "MGZ-7F42K")
        self.assertEqual(body["status"], "confirmed")
        self.assertEqual(body["court"]["name"], "Court 1")
        self.assertEqual(body["start_times"], ["18:00", "19:00"])
        self.assertEqual(body["attendee_names"], ["Ahmed Hassan", "Omar Ali"])
        self.assertEqual(body["price_egp"], 350)
        self.assertIn("/pass/MGZ-7F42K", body["qr_payload"])

        lower = self.client.get("/api/v1/passes/mgz-7f42k")
        self.assertEqual(lower.status_code, 200)
        self.assertEqual(lower.json()["booking_code"], "MGZ-7F42K")

        redeemed = self._booking(
            status=Booking.Status.REDEEMED,
            booking_code="MGZ-2K91P",
            redeemed_at=timezone.now(),
        )
        self._slot(redeemed, start=time(20, 0))
        redeemed_response = self.client.get("/api/v1/passes/MGZ-2K91P")
        self.assertEqual(redeemed_response.status_code, 200)
        self.assertEqual(redeemed_response.json()["status"], "redeemed")
        self.assertIsNotNone(redeemed_response.json()["redeemed_at"])

    def test_public_pass_unpaid_and_unknown_are_404(self):
        unpaid_statuses = (
            Booking.Status.HELD,
            Booking.Status.PENDING_PAYMENT,
            Booking.Status.FAILED,
            Booking.Status.CANCELLED,
            Booking.Status.EXPIRED,
        )
        for index, status in enumerate(unpaid_statuses):
            booking = self._booking(
                status=status,
                booking_code=f"MGZ-UNP{index}",
            )
            self._slot(booking, start=time(8 + index, 0))
            response = self.client.get(f"/api/v1/passes/{booking.booking_code}")
            self.assertEqual(response.status_code, 404, status)
            error = response.json()["error"]
            self.assertEqual(error["code"], "NOT_FOUND")
            self.assertEqual(error["message"], "No paid booking for this code.")

        missing = self.client.get("/api/v1/passes/MGZ-XXXXX")
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["message"], "No paid booking for this code.")

    def test_public_pass_route_name(self):
        self.assertEqual(reverse("public-pass", kwargs={"code": "MGZ-7F42K"}), "/api/v1/passes/MGZ-7F42K")
