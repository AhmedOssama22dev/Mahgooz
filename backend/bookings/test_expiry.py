from datetime import time, timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from bookings.expiry import expire_elapsed_holds
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import cairo_today
from bookings.seed import seed_courts


class ExpireElapsedHoldsTests(TestCase):
    def setUp(self):
        seed_courts()
        self.court = Court.objects.get(slug="court-1")
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        self.slot_date = cairo_today() + timedelta(days=5)

    def _booking(self, **overrides):
        payload = {
            "user": self.user,
            "status": Booking.Status.HELD,
            "booker_name": self.user.name,
            "attendee_names": ["Ahmed Hassan"],
            "total_price_egp": 350,
            "total_price_cents": 35000,
            "hold_expires_at": timezone.now() - timedelta(minutes=1),
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

    def test_expires_unpaid_hold_and_releases_all_slots(self):
        booking = self._booking()
        self._slot(booking, start=time(18, 0))
        self._slot(booking, start=time(19, 0))

        self.assertEqual(expire_elapsed_holds(), 1)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertEqual(booking.slots.filter(released_at__isnull=True).count(), 0)
        self.assertEqual(booking.slots.filter(released_at__isnull=False).count(), 2)

    def test_expires_pending_payment(self):
        booking = self._booking(status=Booking.Status.PENDING_PAYMENT)
        self._slot(booking)

        expire_elapsed_holds()

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertIsNotNone(booking.slots.get().released_at)

    def test_does_not_expire_confirmed_even_if_ttl_elapsed(self):
        booking = self._booking(status=Booking.Status.CONFIRMED)
        self._slot(booking)

        self.assertEqual(expire_elapsed_holds(), 0)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.CONFIRMED)
        self.assertIsNone(booking.slots.get().released_at)

    def test_live_hold_is_left_alone(self):
        booking = self._booking(hold_expires_at=timezone.now() + timedelta(minutes=10))
        self._slot(booking)

        self.assertEqual(expire_elapsed_holds(), 0)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.HELD)
        self.assertIsNone(booking.slots.get().released_at)

    def test_command_expires_unpaid_holds(self):
        booking = self._booking()
        self._slot(booking)
        out = StringIO()

        call_command("expire_holds", stdout=out)

        booking.refresh_from_db()
        self.assertEqual(booking.status, Booking.Status.EXPIRED)
        self.assertIn("Expired 1 unpaid hold", out.getvalue())
