from datetime import time, timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from accounts.models import User
from bookings.errors import slot_taken
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import cairo_today
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
        self.assertEqual(by_start["19:00"]["state"], "held")
        self.assertEqual(by_start["20:00"]["state"], "booked")
        self.assertEqual(by_start["21:00"]["state"], "booked")
        self.assertEqual(by_start["17:00"]["state"], "available")

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
        self.assertEqual(reverse("staff-login"), "/api/v1/staff/login")
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
