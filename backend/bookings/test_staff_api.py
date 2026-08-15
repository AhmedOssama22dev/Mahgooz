from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta

from django.db import connections
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase

from accounts.models import User
from accounts.tokens import issue_tokens
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import cairo_today
from bookings.seed import seed_courts

STAFF_LIST_URL = "/api/v1/staff/bookings"
STAFF_PASS_URL = "/api/v1/staff/passes/{code}"
STAFF_REDEEM_URL = "/api/v1/staff/passes/{code}/redeem"


class StaffApiTests(APITestCase):
    def setUp(self):
        seed_courts()
        self.court = Court.objects.get(slug="court-1")
        self.other_court = Court.objects.get(slug="court-2")
        self.today = cairo_today()
        self.tomorrow = self.today + timedelta(days=1)
        self.customer = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        self.staff = User.objects.create_user(
            phone="01000000000",
            name="Mostafa",
            password="staffpass",
            is_staff=True,
        )
        self._auth(self.staff)

    def _auth(self, user):
        tokens = issue_tokens(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def _clear_auth(self):
        self.client.credentials()

    def _booking(self, **overrides):
        payload = {
            "user": self.customer,
            "status": Booking.Status.CONFIRMED,
            "booker_name": self.customer.name,
            "attendee_names": ["Ahmed Hassan", "Omar Ali"],
            "total_price_egp": 350,
            "total_price_cents": 35000,
            "booking_code": "MGZ-7F42K",
        }
        payload.update(overrides)
        return Booking.objects.create(**payload)

    def _slot(self, booking, start=time(18, 0), court=None, date=None, **overrides):
        payload = {
            "booking": booking,
            "court": court or self.court,
            "date": date or self.today,
            "start_time": start,
            "price_egp": 350,
            "price_cents": 35000,
        }
        payload.update(overrides)
        return BookingSlot.objects.create(**payload)

    def test_unauthenticated_staff_routes_are_401(self):
        booking = self._booking()
        self._slot(booking)
        self._clear_auth()
        for method, url in (
            ("get", STAFF_LIST_URL),
            ("get", STAFF_PASS_URL.format(code=booking.booking_code)),
            ("post", STAFF_REDEEM_URL.format(code=booking.booking_code)),
        ):
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 401, url)
            self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")

    def test_customer_jwt_is_forbidden_on_all_staff_routes(self):
        booking = self._booking()
        self._slot(booking)
        self._auth(self.customer)
        for method, url in (
            ("get", STAFF_LIST_URL),
            ("get", STAFF_PASS_URL.format(code=booking.booking_code)),
            ("post", STAFF_REDEEM_URL.format(code=booking.booking_code)),
        ):
            response = getattr(self.client, method)(url)
            self.assertEqual(response.status_code, 403, url)
            error = response.json()["error"]
            self.assertEqual(error["code"], "FORBIDDEN")
            self.assertEqual(error["message"], "Staff token required.")

    def test_staff_login_endpoint_unlocks_staff_list(self):
        self._clear_auth()
        login = self.client.post(
            "/api/v1/auth/login",
            {"phone": "01000000000", "password": "staffpass"},
            format="json",
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["user"]["role"], "staff")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
        response = self.client.get(STAFF_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["date"], self.today.isoformat())
        self.assertEqual(response.json()["bookings"], [])

    def test_list_returns_paid_bookings_with_all_child_slots(self):
        paid = self._booking(total_price_egp=700, total_price_cents=70000)
        self._slot(paid, start=time(18, 0))
        self._slot(paid, start=time(19, 0))
        redeemed = self._booking(
            status=Booking.Status.REDEEMED,
            booking_code="MGZ-RED01",
            redeemed_at=timezone.now(),
            total_price_egp=350,
            total_price_cents=35000,
        )
        self._slot(redeemed, start=time(10, 0))
        held = self._booking(status=Booking.Status.HELD, booking_code="MGZ-HELD1")
        self._slot(held, start=time(20, 0))
        pending = self._booking(
            status=Booking.Status.PENDING_PAYMENT,
            booking_code="MGZ-PEND1",
        )
        self._slot(pending, start=time(21, 0))
        other_day = self._booking(booking_code="MGZ-NEXT1")
        self._slot(other_day, date=self.tomorrow, start=time(18, 0))

        response = self.client.get(STAFF_LIST_URL, {"date": self.today.isoformat()})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["date"], self.today.isoformat())
        codes = [item["booking_code"] for item in body["bookings"]]
        self.assertEqual(codes, ["MGZ-RED01", "MGZ-7F42K"])
        paid_item = body["bookings"][1]
        self.assertEqual(paid_item["status"], "confirmed")
        self.assertEqual(paid_item["court_name"], "Court 1")
        self.assertEqual(paid_item["start_time"], "18:00")
        self.assertEqual(paid_item["end_time"], "20:00")
        self.assertEqual(len(paid_item["slots"]), 2)
        self.assertEqual(
            [slot["start_time"] for slot in paid_item["slots"]],
            ["18:00", "19:00"],
        )

    def test_list_defaults_to_today_and_filters_by_date(self):
        today_booking = self._booking()
        self._slot(today_booking)
        tomorrow_booking = self._booking(booking_code="MGZ-NEXT1")
        self._slot(tomorrow_booking, date=self.tomorrow)

        defaulted = self.client.get(STAFF_LIST_URL)
        self.assertEqual(defaulted.status_code, 200)
        self.assertEqual(defaulted.json()["date"], self.today.isoformat())
        self.assertEqual(
            [item["booking_code"] for item in defaulted.json()["bookings"]],
            ["MGZ-7F42K"],
        )

        filtered = self.client.get(STAFF_LIST_URL, {"date": self.tomorrow.isoformat()})
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual(filtered.json()["date"], self.tomorrow.isoformat())
        self.assertEqual(
            [item["booking_code"] for item in filtered.json()["bookings"]],
            ["MGZ-NEXT1"],
        )

    def test_list_rejects_invalid_date(self):
        response = self.client.get(STAFF_LIST_URL, {"date": "not-a-date"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    def test_lookup_confirmed_today_can_redeem(self):
        booking = self._booking(paymob_transaction_id="txn-289187034")
        self._slot(booking)
        self._slot(booking, start=time(19, 0), price_egp=350, price_cents=35000)
        response = self.client.get(STAFF_PASS_URL.format(code="mgz-7f42k"))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["booking_code"], "MGZ-7F42K")
        self.assertEqual(body["status"], "confirmed")
        self.assertTrue(body["can_redeem"])
        self.assertEqual(body["booker_phone"], "01012345678")
        self.assertEqual(body["paymob_transaction_id"], "txn-289187034")
        self.assertEqual(len(body["slots"]), 2)
        self.assertEqual(body["court"]["name"], "Court 1")
        self.assertEqual(body["date"], self.today.isoformat())
        self.assertEqual(body["start_time"], "18:00")
        self.assertEqual(body["end_time"], "20:00")

    def test_lookup_redeemed_returns_200(self):
        booking = self._booking(
            status=Booking.Status.REDEEMED,
            redeemed_at=timezone.now(),
        )
        self._slot(booking)
        response = self.client.get(STAFF_PASS_URL.format(code=booking.booking_code))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "redeemed")
        self.assertFalse(body["can_redeem"])
        self.assertIsNotNone(body["redeemed_at"])

    def test_lookup_unknown_code_is_404(self):
        response = self.client.get(STAFF_PASS_URL.format(code="MGZ-NONE1"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertEqual(response.json()["error"]["message"], "No booking for this code.")

    def test_lookup_pending_and_failed_are_409(self):
        pending = self._booking(
            status=Booking.Status.PENDING_PAYMENT,
            booking_code="MGZ-PEND1",
        )
        self._slot(pending)
        failed = self._booking(status=Booking.Status.FAILED, booking_code="MGZ-FAIL1")
        self._slot(failed, start=time(19, 0))
        for code in ("MGZ-PEND1", "MGZ-FAIL1"):
            response = self.client.get(STAFF_PASS_URL.format(code=code))
            self.assertEqual(response.status_code, 409, code)
            self.assertEqual(response.json()["error"]["code"], "PAYMENT_NOT_CONFIRMED")

    def test_lookup_cancelled_is_404(self):
        booking = self._booking(status=Booking.Status.CANCELLED, booking_code="MGZ-CANC1")
        self._slot(booking)
        response = self.client.get(STAFF_PASS_URL.format(code="MGZ-CANC1"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_redeem_confirmed_today_sets_redeemed_at_and_keeps_slots(self):
        booking = self._booking()
        self._slot(booking, start=time(18, 0))
        self._slot(booking, start=time(19, 0))
        response = self.client.post(STAFF_REDEEM_URL.format(code=booking.booking_code))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "redeemed")
        self.assertFalse(body["can_redeem"])
        self.assertIsNotNone(body["redeemed_at"])
        self.assertEqual(len(body["slots"]), 2)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.REDEEMED)
        self.assertIsNotNone(booking.redeemed_at)
        self.assertEqual(
            BookingSlot.objects.filter(booking=booking, released_at__isnull=True).count(),
            2,
        )

    def test_redeem_twice_is_already_redeemed(self):
        booking = self._booking()
        self._slot(booking)
        first = self.client.post(STAFF_REDEEM_URL.format(code=booking.booking_code))
        self.assertEqual(first.status_code, 200)
        second = self.client.post(STAFF_REDEEM_URL.format(code=booking.booking_code))
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"]["code"], "ALREADY_REDEEMED")
        self.assertIn("already redeemed at", second.json()["error"]["message"])

    def test_redeem_pending_and_failed_are_409(self):
        pending = self._booking(
            status=Booking.Status.PENDING_PAYMENT,
            booking_code="MGZ-PEND1",
        )
        self._slot(pending)
        failed = self._booking(status=Booking.Status.FAILED, booking_code="MGZ-FAIL1")
        self._slot(failed, start=time(19, 0))
        for code in ("MGZ-PEND1", "MGZ-FAIL1"):
            response = self.client.post(STAFF_REDEEM_URL.format(code=code))
            self.assertEqual(response.status_code, 409, code)
            self.assertEqual(response.json()["error"]["code"], "PAYMENT_NOT_CONFIRMED")

    def test_redeem_wrong_day_leaves_confirmed(self):
        booking = self._booking()
        self._slot(booking, date=self.tomorrow)
        response = self.client.post(STAFF_REDEEM_URL.format(code=booking.booking_code))
        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(error["code"], "WRONG_DAY")
        self.assertIn("not today", error["message"])
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertIsNone(booking.redeemed_at)

    def test_redeem_unknown_code_is_404(self):
        response = self.client.post(STAFF_REDEEM_URL.format(code="MGZ-NONE1"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")


def _threaded_redeem(token, code):
    connections.close_all()
    try:
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post(
            STAFF_REDEEM_URL.format(code=code),
            {},
            format="json",
        )
        return response.status_code, response.json()
    finally:
        connections.close_all()


class ConcurrentRedeemTests(TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        seed_courts()
        self.court = Court.objects.get(slug="court-1")
        self.customer = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        self.staff_a = User.objects.create_user(
            phone="01000000000",
            name="Mostafa",
            password="staffpass",
            is_staff=True,
        )
        self.staff_b = User.objects.create_user(
            phone="01000000001",
            name="Sara",
            password="staffpass",
            is_staff=True,
        )
        self.booking = Booking.objects.create(
            user=self.customer,
            status=Booking.Status.CONFIRMED,
            booker_name=self.customer.name,
            attendee_names=["Ahmed Hassan"],
            total_price_egp=350,
            total_price_cents=35000,
            booking_code="MGZ-7F42K",
        )
        BookingSlot.objects.create(
            booking=self.booking,
            court=self.court,
            date=cairo_today(),
            start_time=time(18, 0),
            price_egp=350,
            price_cents=35000,
        )

    def tearDown(self):
        connections.close_all()
        super().tearDown()

    def test_simultaneous_redeems_one_winner(self):
        token_a = issue_tokens(self.staff_a)["access"]
        token_b = issue_tokens(self.staff_b)["access"]
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(_threaded_redeem, token_a, "MGZ-7F42K")
            future_b = pool.submit(_threaded_redeem, token_b, "MGZ-7F42K")
            results = [future_a.result(), future_b.result()]
        connections.close_all()
        codes = sorted(status for status, _body in results)
        self.assertEqual(codes, [200, 409])
        winner = next(body for status, body in results if status == 200)
        loser = next(body for status, body in results if status == 409)
        self.assertEqual(winner["status"], "redeemed")
        self.assertIsNotNone(winner["redeemed_at"])
        self.assertEqual(loser["error"]["code"], "ALREADY_REDEEMED")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.Status.REDEEMED)
        self.assertIsNotNone(self.booking.redeemed_at)
        self.assertEqual(
            Booking.objects.filter(status=Booking.Status.REDEEMED).count(),
            1,
        )
