from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework.views import APIView

from bookings.errors import slot_taken
from bookings.models import Court
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


class RouteContractTests(APITestCase):
    def test_slots_registered_as_not_implemented(self):
        response = self.client.get("/api/v1/slots")
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.json()["error"]["code"], "NOT_IMPLEMENTED")
        self.assertEqual(
            set(response.json()["error"].keys()),
            {"code", "message"},
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
