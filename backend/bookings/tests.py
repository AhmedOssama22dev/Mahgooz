from datetime import date, time

from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking, BookingSlot, Court
from bookings.pricing import price_for_start_time
from bookings.seed import seed_courts

SLOT_DATE = date(2026, 8, 20)


class PricingTests(TestCase):
    def test_morning_band(self):
        result = price_for_start_time(time(8, 0))
        self.assertEqual(result["period"], "morning")
        self.assertEqual(result["price_egp"], 200)
        self.assertEqual(result["price_cents"], 20000)
        self.assertEqual(result["label"], "Morning available")

    def test_afternoon_band(self):
        result = price_for_start_time("12:00")
        self.assertEqual(result["period"], "afternoon")
        self.assertEqual(result["price_egp"], 280)
        self.assertEqual(result["price_cents"], 28000)

    def test_evening_band_start(self):
        result = price_for_start_time(time(17, 0))
        self.assertEqual(result["period"], "evening")
        self.assertEqual(result["price_egp"], 350)
        self.assertEqual(result["price_cents"], 35000)

    def test_last_bookable_start(self):
        result = price_for_start_time(time(21, 0))
        self.assertEqual(result["period"], "evening")
        self.assertEqual(result["price_egp"], 350)


class SeedCourtsTests(TestCase):
    def test_seed_is_idempotent(self):
        first = seed_courts()
        second = seed_courts()
        self.assertEqual(Court.objects.count(), 2)
        self.assertEqual(
            list(Court.objects.order_by("sort_order").values_list("name", "slug")),
            [("Court 1", "court-1"), ("Court 2", "court-2")],
        )
        self.assertEqual({court.slug for court in first}, {"court-1", "court-2"})
        self.assertEqual({court.id for court in first}, {court.id for court in second})


class BookingConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        seed_courts()
        self.court1 = Court.objects.get(slug="court-1")
        self.court2 = Court.objects.get(slug="court-2")

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

    def _slot(self, booking, court=None, start=time(18, 0), released_at=None, **overrides):
        payload = {
            "booking": booking,
            "court": court or self.court1,
            "date": SLOT_DATE,
            "start_time": start,
            "price_egp": 350,
            "price_cents": 35000,
            "released_at": released_at,
        }
        payload.update(overrides)
        return BookingSlot.objects.create(**payload)

    def test_second_unreleased_slot_same_court_time_raises(self):
        self._slot(self._booking())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._slot(self._booking())

    def test_released_slot_does_not_block_new_unreleased(self):
        self._slot(self._booking(), released_at=timezone.now())
        self._slot(self._booking())
        self.assertEqual(
            BookingSlot.objects.filter(
                court=self.court1,
                date=SLOT_DATE,
                start_time=time(18, 0),
            ).count(),
            2,
        )

    def test_same_time_on_other_court_allowed(self):
        self._slot(self._booking(), court=self.court1)
        self._slot(self._booking(), court=self.court2)
        self.assertEqual(BookingSlot.objects.count(), 2)

    def test_one_booking_can_hold_two_hours(self):
        booking = self._booking(total_price_egp=700, total_price_cents=70000)
        self._slot(booking, start=time(18, 0))
        self._slot(booking, start=time(19, 0))
        self.assertEqual(booking.slots.count(), 2)

    def test_duplicate_hour_on_same_booking_raises(self):
        booking = self._booking()
        self._slot(booking, start=time(18, 0))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._slot(booking, start=time(18, 0))

    def test_duplicate_booking_code_raises(self):
        self._booking(booking_code="MGZ-7F42K")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._booking(booking_code="MGZ-7F42K")

    def test_duplicate_paymob_intention_id_raises(self):
        self._booking(paymob_intention_id="int-1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._booking(paymob_intention_id="int-1")

    def test_duplicate_paymob_transaction_id_raises(self):
        self._booking(paymob_transaction_id="txn-1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._booking(paymob_transaction_id="txn-1")

    def test_multiple_null_paymob_ids_allowed(self):
        first = self._booking()
        second = self._booking()
        self.assertIsNone(first.paymob_intention_id)
        self.assertIsNone(second.paymob_transaction_id)
        self.assertEqual(Booking.objects.filter(paymob_intention_id__isnull=True).count(), 2)

    def test_partial_unique_index_exists_in_postgres(self):
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexdef FROM pg_indexes WHERE indexname = %s",
                ["uniq_active_court_slot"],
            )
            row = cursor.fetchone()
        self.assertIsNotNone(row)
        definition = row[0].lower()
        self.assertIn("unique", definition)
        self.assertIn("released_at", definition)
        self.assertIn("is null", definition)
        self.assertIn("court_id", definition)
        self.assertIn("start_time", definition)
