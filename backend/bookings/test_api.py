from concurrent.futures import ThreadPoolExecutor
from datetime import time, timedelta
from uuid import uuid4

from django.db import connections
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient, APITestCase
from rest_framework.views import APIView

from accounts.models import User
from accounts.tokens import issue_tokens
from bookings.errors import slot_taken
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import cairo_today
from bookings.seed import seed_courts
from config.exceptions import APIError, api_exception_handler


class CourtListApiTests(APITestCase):
    def test_lists_seeded_courts(self):
        response = self.client.get("/api/v1/courts")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        names = [court["name"] for court in body]
        self.assertEqual(names, ["Court 1", "Court 2"])
        self.assertEqual({court["slug"] for court in body}, {"court-1", "court-2"})
        self.assertEqual(Court.objects.count(), 2)
        for court in body:
            self.assertEqual(set(court.keys()), {"id", "name", "slug"})

    def test_courts_are_public(self):
        response = self.client.get("/api/v1/courts")
        self.assertEqual(response.status_code, 200)


class SlotListApiTests(APITestCase):
    def setUp(self):
        self.court = Court.objects.get(slug="court-1")
        self.other_court = Court.objects.get(slug="court-2")
        self.slot_date = cairo_today() + timedelta(days=5)
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )

    def _slots(self, **query):
        params = {"date": self.slot_date.isoformat(), "court_id": str(self.court.id)}
        params.update(query)
        params = {key: value for key, value in params.items() if value is not None}
        return self.client.get("/api/v1/slots", params)

    def _by_start(self, body):
        return {slot["start_time"]: slot for slot in body["slots"]}

    def _booking(self, **overrides):
        payload = {
            "user": self.user,
            "status": Booking.Status.HELD,
            "booker_name": self.user.name,
            "attendee_names": ["Ahmed Hassan"],
            "total_price_egp": 350,
            "total_price_cents": 35000,
        }
        payload.update(overrides)
        return Booking.objects.create(**payload)

    def _slot(self, booking, start=time(18, 0), court=None, **overrides):
        payload = {
            "booking": booking,
            "court": court or self.court,
            "date": self.slot_date,
            "start_time": start,
            "price_egp": 350,
            "price_cents": 35000,
        }
        payload.update(overrides)
        return BookingSlot.objects.create(**payload)

    def test_empty_day_is_full_available_grid(self):
        response = self._slots()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["date"], self.slot_date.isoformat())
        self.assertEqual(body["court"], {"id": str(self.court.id), "name": "Court 1"})
        self.assertEqual(body["operating_hours"], {"open": "08:00", "close": "22:00"})
        self.assertEqual(body["slot_minutes"], 60)
        self.assertEqual(len(body["slots"]), 14)
        self.assertEqual(body["slots"][0]["start_time"], "08:00")
        self.assertEqual(body["slots"][0]["end_time"], "09:00")
        self.assertEqual(body["slots"][-1]["start_time"], "21:00")
        self.assertEqual(body["slots"][-1]["end_time"], "22:00")
        self.assertTrue(all(slot["state"] == "available" for slot in body["slots"]))

    def test_slots_are_public(self):
        response = self._slots()
        self.assertEqual(response.status_code, 200)

    def test_pricing_boundaries_and_morning_label(self):
        body = self._slots().json()
        by_start = self._by_start(body)

        for start in ("08:00", "11:00"):
            self.assertEqual(by_start[start]["period"], "morning")
            self.assertEqual(by_start[start]["price_egp"], 200)
            self.assertEqual(by_start[start]["price_cents"], 20000)
            self.assertEqual(by_start[start]["label"], "Morning available")

        noon = by_start["12:00"]
        self.assertEqual(noon["period"], "afternoon")
        self.assertEqual(noon["price_egp"], 280)
        self.assertEqual(noon["price_cents"], 28000)
        self.assertIsNone(noon["label"])

        for start in ("17:00", "21:00"):
            self.assertEqual(by_start[start]["period"], "evening")
            self.assertEqual(by_start[start]["price_egp"], 350)
            self.assertEqual(by_start[start]["price_cents"], 35000)
            self.assertIsNone(by_start[start]["label"])

    def test_missing_date_is_validation_error(self):
        response = self._slots(date=None)
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "VALIDATION_ERROR")
        self.assertEqual(error["message"], "Invalid query parameters")
        self.assertIn("date", error["details"])

    def test_missing_court_id_is_validation_error(self):
        response = self._slots(court_id=None)
        self.assertEqual(response.status_code, 400)
        error = response.json()["error"]
        self.assertEqual(error["code"], "VALIDATION_ERROR")
        self.assertIn("court_id", error["details"])

    def test_invalid_date_format(self):
        response = self._slots(date="20-08-2026")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")

    def test_yesterday_is_out_of_range(self):
        response = self._slots(date=(cairo_today() - timedelta(days=1)).isoformat())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "DATE_OUT_OF_RANGE")

    def test_day_15_is_out_of_range(self):
        response = self._slots(date=(cairo_today() + timedelta(days=15)).isoformat())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "DATE_OUT_OF_RANGE")

    def test_unknown_court_is_not_found(self):
        response = self._slots(court_id=str(uuid4()))
        self.assertEqual(response.status_code, 404)
        error = response.json()["error"]
        self.assertEqual(error["code"], "NOT_FOUND")
        self.assertEqual(error["message"], "Court not found.")

    def test_maps_live_hold_and_confirmed_states(self):
        self._slot(
            self._booking(
                status=Booking.Status.HELD,
                hold_expires_at=timezone.now() + timedelta(minutes=10),
            ),
            start=time(18, 0),
        )
        self._slot(
            self._booking(status=Booking.Status.PENDING_PAYMENT),
            start=time(19, 0),
        )
        self._slot(
            self._booking(status=Booking.Status.CONFIRMED),
            start=time(20, 0),
        )
        self._slot(
            self._booking(status=Booking.Status.REDEEMED),
            start=time(21, 0),
        )

        by_start = self._by_start(self._slots().json())
        self.assertEqual(by_start["18:00"]["state"], "held")
        self.assertFalse(by_start["18:00"]["held_by_me"])
        self.assertEqual(by_start["19:00"]["state"], "held")
        self.assertFalse(by_start["19:00"]["held_by_me"])
        self.assertEqual(by_start["20:00"]["state"], "booked")
        self.assertFalse(by_start["20:00"]["held_by_me"])
        self.assertEqual(by_start["21:00"]["state"], "booked")
        self.assertEqual(by_start["17:00"]["state"], "available")
        self.assertFalse(by_start["17:00"]["held_by_me"])

    def test_holder_sees_own_unpaid_slots_as_held_by_me(self):
        self._slot(
            self._booking(
                status=Booking.Status.HELD,
                hold_expires_at=timezone.now() + timedelta(minutes=10),
            ),
            start=time(18, 0),
        )
        tokens = issue_tokens(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        mine = self._by_start(self._slots().json())
        self.assertEqual(mine["18:00"]["state"], "held")
        self.assertTrue(mine["18:00"]["held_by_me"])

        stranger = User.objects.create_user(
            phone="01098765432",
            name="Omar Ali",
            password="secret12",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {issue_tokens(stranger)['access']}"
        )
        other = self._by_start(self._slots().json())
        self.assertEqual(other["18:00"]["state"], "held")
        self.assertFalse(other["18:00"]["held_by_me"])

    def test_expired_hold_is_released_on_list(self):
        booking = self._booking(
            status=Booking.Status.HELD,
            hold_expires_at=timezone.now() - timedelta(minutes=1),
        )
        self._slot(booking, start=time(18, 0))

        by_start = self._by_start(self._slots().json())
        self.assertEqual(by_start["18:00"]["state"], "available")

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertIsNotNone(booking.slots.get().released_at)


class RouteContractTests(APITestCase):
    def test_slots_require_query_params(self):
        response = self.client.get("/api/v1/slots")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(
            set(response.json()["error"].keys()),
            {"code", "message", "details"},
        )

    def test_named_routes_reverse_under_api_v1(self):
        self.assertEqual(reverse("courts"), "/api/v1/courts")
        self.assertEqual(reverse("slots"), "/api/v1/slots")
        self.assertEqual(reverse("booking-hold"), "/api/v1/bookings/hold")
        self.assertEqual(reverse("booking-list"), "/api/v1/bookings")
        self.assertEqual(reverse("staff-bookings"), "/api/v1/staff/bookings")
        self.assertEqual(reverse("paymob-webhook"), "/api/v1/webhooks/paymob")
        self.assertEqual(
            reverse("public-pass", kwargs={"code": "MGZ-7F42K"}),
            "/api/v1/passes/MGZ-7F42K",
        )


class ErrorEnvelopeTests(APITestCase):
    def test_api_error_envelope(self):
        try:
            slot_taken(
                [
                    {
                        "court_id": "11111111-1111-4111-8111-111111111111",
                        "date": "2026-08-20",
                        "start_time": "18:00",
                    }
                ]
            )
        except APIError as exc:
            response = api_exception_handler(exc, {"view": APIView()})
        self.assertEqual(response.status_code, 409)
        body = response.data
        self.assertEqual(body["error"]["code"], "SLOT_TAKEN")
        self.assertIn("None of the requested slots were held", body["error"]["message"])
        self.assertEqual(
            body["error"]["details"]["conflicting_slots"][0]["start_time"],
            "18:00",
        )


class HoldCancelApiTests(APITestCase):
    hold_url = "/api/v1/bookings/hold"

    def setUp(self):
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

    def _slot_payload(self, start, court=None, date=None):
        return {
            "court_id": str((court or self.court).id),
            "date": (date or self.slot_date).isoformat(),
            "start_time": start,
        }

    def _hold_payload(self, starts, attendees=None, court=None, date=None):
        if attendees is None:
            attendees = ["Ahmed Hassan", "Omar Ali"]
        return {
            "slots": [self._slot_payload(start, court=court, date=date) for start in starts],
            "attendee_names": attendees,
        }

    def _hold(self, starts=("18:00", "19:00"), **kwargs):
        return self.client.post(
            self.hold_url,
            self._hold_payload(starts, **kwargs),
            format="json",
        )

    def _booking(self, **overrides):
        payload = {
            "user": self.user,
            "status": Booking.Status.HELD,
            "booker_name": self.user.name,
            "attendee_names": ["Ahmed Hassan"],
            "total_price_egp": 350,
            "total_price_cents": 35000,
            "hold_expires_at": timezone.now() + timedelta(minutes=10),
        }
        payload.update(overrides)
        return Booking.objects.create(**payload)

    def _slot(self, booking, start=time(18, 0), court=None, **overrides):
        payload = {
            "booking": booking,
            "court": court or self.court,
            "date": self.slot_date,
            "start_time": start,
            "price_egp": 350,
            "price_cents": 35000,
        }
        payload.update(overrides)
        return BookingSlot.objects.create(**payload)

    def test_multi_slot_hold_returns_normalized_slots_and_summed_price(self):
        before = timezone.now()
        response = self._hold()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["status"], "held")
        self.assertEqual(body["booker_name"], "Ahmed Hassan")
        self.assertEqual(body["attendee_names"], ["Ahmed Hassan", "Omar Ali"])
        self.assertEqual(body["total_price_egp"], 700)
        self.assertEqual(body["total_price_cents"], 70000)
        self.assertIsNone(body["booking_code"])
        self.assertIsNone(body["qr_payload"])
        self.assertEqual(len(body["slots"]), 2)
        self.assertEqual(body["slots"][0]["start_time"], "18:00")
        self.assertEqual(body["slots"][0]["end_time"], "19:00")
        self.assertEqual(body["slots"][1]["start_time"], "19:00")
        self.assertEqual(body["slots"][1]["end_time"], "20:00")
        self.assertEqual(body["slots"][0]["price_egp"], 350)
        expires = parse_datetime(body["hold_expires_at"])
        self.assertAlmostEqual((expires - before).total_seconds(), 10 * 60, delta=15)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(BookingSlot.objects.filter(released_at__isnull=True).count(), 2)

    def test_unauthenticated_hold_is_401(self):
        self.client.credentials()
        response = self._hold()
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "UNAUTHENTICATED")
        self.assertEqual(Booking.objects.count(), 0)

    def test_empty_attendee_name_is_validation_error(self):
        response = self._hold(attendees=["Ahmed Hassan", "  "])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(Booking.objects.count(), 0)

    def test_no_attendees_is_validation_error(self):
        response = self._hold(attendees=[])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(Booking.objects.count(), 0)

    def test_too_many_attendees_is_validation_error(self):
        response = self._hold(
            attendees=["A", "B", "C", "D", "E"],
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(Booking.objects.count(), 0)

    def test_mixed_courts_rejected(self):
        payload = {
            "slots": [
                self._slot_payload("18:00"),
                self._slot_payload("19:00", court=self.other_court),
            ],
            "attendee_names": ["Ahmed Hassan"],
        }
        response = self.client.post(self.hold_url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "MIXED_SLOTS")
        self.assertEqual(Booking.objects.count(), 0)

    def test_mixed_dates_rejected(self):
        payload = {
            "slots": [
                self._slot_payload("18:00"),
                self._slot_payload("19:00", date=self.slot_date + timedelta(days=1)),
            ],
            "attendee_names": ["Ahmed Hassan"],
        }
        response = self.client.post(self.hold_url, payload, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "MIXED_SLOTS")
        self.assertEqual(Booking.objects.count(), 0)

    def test_duplicate_hour_rejected(self):
        response = self._hold(starts=("18:00", "18:00"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "DUPLICATE_SLOTS")
        self.assertEqual(Booking.objects.count(), 0)

    def test_past_slot_rejected(self):
        response = self._hold(starts=("08:00",), date=cairo_today())
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "PAST_SLOT")
        self.assertEqual(Booking.objects.count(), 0)

    def test_day_15_is_out_of_range(self):
        response = self._hold(starts=("18:00",), date=cairo_today() + timedelta(days=15))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "DATE_OUT_OF_RANGE")
        self.assertEqual(Booking.objects.count(), 0)

    def test_same_user_rehold_returns_existing_booking(self):
        first = self._hold(starts=("18:00", "19:00"))
        self.assertEqual(first.status_code, 201)
        booking_id = first.json()["id"]
        expires = first.json()["hold_expires_at"]
        second = self._hold(starts=("18:00", "19:00"))
        self.assertEqual(second.status_code, 201)
        self.assertEqual(second.json()["id"], booking_id)
        self.assertEqual(second.json()["hold_expires_at"], expires)
        self.assertEqual(Booking.objects.filter(user=self.user).count(), 1)
        self.assertEqual(
            BookingSlot.objects.filter(released_at__isnull=True).count(),
            2,
        )

    def test_same_user_can_replace_overlapping_hold(self):
        first = self._hold(starts=("18:00",))
        self.assertEqual(first.status_code, 201)
        old_id = first.json()["id"]
        second = self._hold(starts=("18:00", "19:00"))
        self.assertEqual(second.status_code, 201)
        self.assertNotEqual(second.json()["id"], old_id)
        old = Booking.objects.get(pk=old_id)
        self.assertEqual(old.status, Booking.Status.CANCELLED)
        self.assertIsNotNone(old.slots.get().released_at)
        self.assertEqual(len(second.json()["slots"]), 2)
        self.assertEqual(Booking.objects.filter(status=Booking.Status.HELD).count(), 1)

    def test_overlapping_hold_is_slot_taken_with_no_partial_hold(self):
        first = self._hold(starts=("18:00", "19:00"))
        self.assertEqual(first.status_code, 201)
        self._auth(self.other)
        second = self._hold(starts=("19:00", "20:00"))
        self.assertEqual(second.status_code, 409)
        error = second.json()["error"]
        self.assertEqual(error["code"], "SLOT_TAKEN")
        self.assertIn("None of the requested slots were held", error["message"])
        starts = [item["start_time"] for item in error["details"]["conflicting_slots"]]
        self.assertIn("19:00", starts)
        self.assertEqual(Booking.objects.filter(user=self.other).count(), 0)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(
            BookingSlot.objects.filter(released_at__isnull=True).count(),
            2,
        )

    def test_expired_hold_is_released_and_can_be_reheld(self):
        stale = self._booking(hold_expires_at=timezone.now() - timedelta(minutes=1))
        self._slot(stale, start=time(18, 0))
        self._auth(self.other)
        response = self._hold(starts=("18:00",))
        self.assertEqual(response.status_code, 201)
        stale.refresh_from_db()
        self.assertEqual(stale.status, Booking.Status.EXPIRED)
        self.assertIsNotNone(stale.slots.get().released_at)
        self.assertEqual(Booking.objects.filter(status=Booking.Status.HELD).count(), 1)

    def test_owner_can_cancel_held_booking_and_slot_becomes_available(self):
        held = self._hold(starts=("18:00",))
        booking_id = held.json()["id"]
        response = self.client.delete(f"/api/v1/bookings/{booking_id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["id"], booking_id)
        self.assertEqual(body["status"], "cancelled")
        self.assertEqual(body["message"], "Slot released.")
        booking = Booking.objects.get(pk=booking_id)
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertIsNotNone(booking.slots.get().released_at)
        self._auth(self.other)
        retry = self._hold(starts=("18:00",))
        self.assertEqual(retry.status_code, 201)

    def test_owner_can_cancel_pending_payment(self):
        booking = self._booking(status=Booking.Status.PENDING_PAYMENT)
        self._slot(booking)
        response = self.client.delete(f"/api/v1/bookings/{booking.id}")
        self.assertEqual(response.status_code, 200)
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CANCELLED)
        self.assertIsNotNone(booking.slots.get().released_at)

    def test_other_user_cannot_cancel(self):
        booking_id = self._hold(starts=("18:00",)).json()["id"]
        self._auth(self.other)
        response = self.client.delete(f"/api/v1/bookings/{booking_id}")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "FORBIDDEN")
        self.assertEqual(response.json()["error"]["message"], "You do not own this booking.")
        booking = Booking.objects.get(pk=booking_id)
        self.assertEqual(booking.status, Booking.Status.HELD)
        self.assertIsNone(booking.slots.get().released_at)

    def test_unknown_booking_is_not_found(self):
        response = self.client.delete(f"/api/v1/bookings/{uuid4()}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")

    def test_confirmed_booking_cannot_be_cancelled(self):
        booking = self._booking(status=Booking.Status.CONFIRMED)
        self._slot(booking)
        response = self.client.delete(f"/api/v1/bookings/{booking.id}")
        self.assertEqual(response.status_code, 409)
        error = response.json()["error"]
        self.assertEqual(error["code"], "CANNOT_CANCEL")
        self.assertIn("Paid bookings cannot be cancelled", error["message"])
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertIsNone(booking.slots.get().released_at)

    def test_redeemed_booking_cannot_be_cancelled(self):
        booking = self._booking(status=Booking.Status.REDEEMED)
        self._slot(booking)
        response = self.client.delete(f"/api/v1/bookings/{booking.id}")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "CANNOT_CANCEL")
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.REDEEMED)
        self.assertIsNone(booking.slots.get().released_at)

    def test_expired_hold_cannot_be_cancelled(self):
        booking = self._booking(hold_expires_at=timezone.now() - timedelta(minutes=1))
        self._slot(booking)
        response = self.client.delete(f"/api/v1/bookings/{booking.id}")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "HOLD_EXPIRED")
        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertIsNotNone(booking.slots.get().released_at)


def _threaded_hold(token, payload):
    connections.close_all()
    try:
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.post("/api/v1/bookings/hold", payload, format="json")
        return response.status_code, response.json()
    finally:
        connections.close_all()


class ConcurrentHoldTests(TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        seed_courts()
        self.court = Court.objects.get(slug="court-1")
        self.slot_date = cairo_today() + timedelta(days=5)
        self.user_a = User.objects.create_user(
            phone="01011111111",
            name="Ahmed Hassan",
            password="secret12",
        )
        self.user_b = User.objects.create_user(
            phone="01022222222",
            name="Omar Ali",
            password="secret12",
        )

    def tearDown(self):
        connections.close_all()
        super().tearDown()

    def _payload(self, starts):
        return {
            "slots": [
                {
                    "court_id": str(self.court.id),
                    "date": self.slot_date.isoformat(),
                    "start_time": start,
                }
                for start in starts
            ],
            "attendee_names": ["Player One"],
        }

    def test_simultaneous_overlapping_holds_one_winner_no_partial(self):
        token_a = issue_tokens(self.user_a)["access"]
        token_b = issue_tokens(self.user_b)["access"]
        payload_a = self._payload(["18:00", "19:00"])
        payload_b = self._payload(["19:00", "20:00"])
        with ThreadPoolExecutor(max_workers=2) as pool:
            future_a = pool.submit(_threaded_hold, token_a, payload_a)
            future_b = pool.submit(_threaded_hold, token_b, payload_b)
            results = [future_a.result(), future_b.result()]
        connections.close_all()
        codes = sorted(status for status, _body in results)
        self.assertEqual(codes, [201, 409])
        winner = next(body for status, body in results if status == 201)
        loser = next(body for status, body in results if status == 409)
        self.assertEqual(loser["error"]["code"], "SLOT_TAKEN")
        self.assertIn("None of the requested slots were held", loser["error"]["message"])
        self.assertEqual(Booking.objects.filter(status=Booking.Status.HELD).count(), 1)
        self.assertEqual(
            BookingSlot.objects.filter(
                court=self.court,
                date=self.slot_date,
                start_time=time(19, 0),
                released_at__isnull=True,
            ).count(),
            1,
        )
        winner_starts = {slot["start_time"] for slot in winner["slots"]}
        self.assertIn("19:00", winner_starts)
        self.assertEqual(
            BookingSlot.objects.filter(booking_id=winner["id"]).count(),
            2,
        )
        self.assertEqual(
            Booking.objects.exclude(id=winner["id"]).count(),
            0,
        )
