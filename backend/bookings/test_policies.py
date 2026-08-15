from datetime import datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from bookings.models import Booking, BookingSlot, Court
from bookings.policies import (
    assert_bookable_date,
    assert_transition,
    cairo_today,
    can_redeem,
    end_time_for,
    generate_booking_code,
    iter_start_times,
    normalize_hold_slots,
    partition_my_bookings,
    qr_payload,
    slot_totals,
)
from bookings.seed import seed_courts
from config.exceptions import APIError
from django.conf import settings


def aware(day, hour, minute=0):
    return timezone.make_aware(
        datetime.combine(day, time(hour, minute)),
        timezone.get_current_timezone(),
    )


class BookingWindowTests(TestCase):
    def test_today_is_bookable(self):
        assert_bookable_date(cairo_today())

    def test_last_window_day_is_bookable(self):
        assert_bookable_date(cairo_today() + timedelta(days=14))

    def test_day_15_is_out_of_range(self):
        with self.assertRaises(APIError) as ctx:
            assert_bookable_date(cairo_today() + timedelta(days=15))
        self.assertEqual(ctx.exception.error_code, "DATE_OUT_OF_RANGE")

    def test_yesterday_is_out_of_range(self):
        with self.assertRaises(APIError) as ctx:
            assert_bookable_date(cairo_today() - timedelta(days=1))
        self.assertEqual(ctx.exception.error_code, "DATE_OUT_OF_RANGE")


class NormalizeHoldSlotsTests(TestCase):
    def setUp(self):
        seed_courts()
        self.court1 = Court.objects.get(slug="court-1")
        self.court2 = Court.objects.get(slug="court-2")
        self.slot_date = cairo_today() + timedelta(days=5)
        self.now = aware(cairo_today(), 8)

    def _slot(self, **overrides):
        payload = {
            "court_id": self.court1.id,
            "date": self.slot_date,
            "start_time": "18:00",
        }
        payload.update(overrides)
        return payload

    def test_two_hours_sum_prices(self):
        normalized = normalize_hold_slots(
            [
                self._slot(start_time="18:00"),
                self._slot(start_time="19:00"),
            ],
            now=self.now,
        )
        self.assertEqual(len(normalized), 2)
        self.assertEqual(slot_totals(normalized), (700, 70000))
        self.assertEqual(normalized[0]["period"], "evening")

    def test_mixed_courts(self):
        with self.assertRaises(APIError) as ctx:
            normalize_hold_slots(
                [
                    self._slot(),
                    self._slot(court_id=self.court2.id, start_time="19:00"),
                ],
                now=self.now,
            )
        self.assertEqual(ctx.exception.error_code, "MIXED_SLOTS")

    def test_mixed_dates(self):
        with self.assertRaises(APIError) as ctx:
            normalize_hold_slots(
                [
                    self._slot(),
                    self._slot(date=self.slot_date + timedelta(days=1), start_time="19:00"),
                ],
                now=self.now,
            )
        self.assertEqual(ctx.exception.error_code, "MIXED_SLOTS")

    def test_duplicate_hour(self):
        with self.assertRaises(APIError) as ctx:
            normalize_hold_slots([self._slot(), self._slot()], now=self.now)
        self.assertEqual(ctx.exception.error_code, "DUPLICATE_SLOTS")

    def test_off_grid(self):
        with self.assertRaises(APIError) as ctx:
            normalize_hold_slots([self._slot(start_time="18:30")], now=self.now)
        self.assertEqual(ctx.exception.error_code, "INVALID_SLOT")

    def test_empty_slots(self):
        with self.assertRaises(APIError) as ctx:
            normalize_hold_slots([], now=self.now)
        self.assertEqual(ctx.exception.error_code, "INVALID_SLOT")

    def test_past_slot_today(self):
        today = cairo_today()
        with self.assertRaises(APIError) as ctx:
            normalize_hold_slots(
                [self._slot(date=today, start_time="18:00")],
                now=aware(today, 18, 30),
            )
        self.assertEqual(ctx.exception.error_code, "PAST_SLOT")


class TransitionTests(TestCase):
    def test_held_to_confirmed_allowed(self):
        booking = Booking(status=Booking.Status.HELD)
        assert_transition(booking, Booking.Status.CONFIRMED)

    def test_confirmed_to_held_rejected(self):
        booking = Booking(status=Booking.Status.CONFIRMED)
        with self.assertRaises(APIError) as ctx:
            assert_transition(booking, Booking.Status.HELD)
        self.assertEqual(ctx.exception.error_code, "INVALID_TRANSITION")


class RedeemPolicyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        seed_courts()
        self.court = Court.objects.get(slug="court-1")

    def _booking(self, status, slot_date):
        booking = Booking.objects.create(
            user=self.user,
            status=status,
            booker_name=self.user.name,
            attendee_names=["Ahmed Hassan"],
            total_price_egp=350,
            total_price_cents=35000,
        )
        BookingSlot.objects.create(
            booking=booking,
            court=self.court,
            date=slot_date,
            start_time=time(18, 0),
            price_egp=350,
            price_cents=35000,
        )
        return booking

    def test_pending_cannot_redeem(self):
        booking = self._booking(Booking.Status.PENDING_PAYMENT, cairo_today())
        self.assertFalse(can_redeem(booking, today=cairo_today()))

    def test_wrong_day_cannot_redeem(self):
        booking = self._booking(Booking.Status.CONFIRMED, cairo_today() + timedelta(days=1))
        self.assertFalse(can_redeem(booking, today=cairo_today()))

    def test_confirmed_today_can_redeem(self):
        booking = self._booking(Booking.Status.CONFIRMED, cairo_today())
        self.assertTrue(can_redeem(booking, today=cairo_today()))


class PartitionMyBookingsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        seed_courts()
        self.court = Court.objects.get(slug="court-1")
        self.today = cairo_today()

    def _booking(self, status, slot_date, start=time(18, 0), released=False, **overrides):
        payload = {
            "user": self.user,
            "status": status,
            "booker_name": self.user.name,
            "attendee_names": ["Ahmed Hassan"],
            "total_price_egp": 350,
            "total_price_cents": 35000,
        }
        payload.update(overrides)
        booking = Booking.objects.create(**payload)
        BookingSlot.objects.create(
            booking=booking,
            court=self.court,
            date=slot_date,
            start_time=start,
            price_egp=350,
            price_cents=35000,
            released_at=aware(slot_date, 8) if released else None,
        )
        return booking

    def test_future_confirmed_is_upcoming(self):
        booking = self._booking(Booking.Status.CONFIRMED, self.today + timedelta(days=1))
        upcoming, past = partition_my_bookings([booking], now=aware(self.today, 8))
        self.assertEqual(upcoming, [booking])
        self.assertEqual(past, [])

    def test_redeemed_is_past(self):
        booking = self._booking(Booking.Status.REDEEMED, self.today + timedelta(days=1))
        upcoming, past = partition_my_bookings([booking], now=aware(self.today, 8))
        self.assertEqual(upcoming, [])
        self.assertEqual(past, [booking])

    def test_yesterday_confirmed_is_past(self):
        booking = self._booking(Booking.Status.CONFIRMED, self.today - timedelta(days=1))
        upcoming, past = partition_my_bookings([booking], now=aware(self.today, 8))
        self.assertEqual(upcoming, [])
        self.assertEqual(past, [booking])

    def test_today_slot_after_end_is_past(self):
        booking = self._booking(Booking.Status.CONFIRMED, self.today, start=time(9, 0))
        upcoming, past = partition_my_bookings([booking], now=aware(self.today, 11))
        self.assertEqual(upcoming, [])
        self.assertEqual(past, [booking])

    def test_today_slot_before_end_is_upcoming(self):
        booking = self._booking(Booking.Status.CONFIRMED, self.today, start=time(18, 0))
        upcoming, past = partition_my_bookings([booking], now=aware(self.today, 11))
        self.assertEqual(upcoming, [booking])
        self.assertEqual(past, [])

    def test_failed_cancelled_expired_are_past_even_if_future_date(self):
        future = self.today + timedelta(days=2)
        failed = self._booking(Booking.Status.FAILED, future, start=time(18, 0), released=True)
        cancelled = self._booking(Booking.Status.CANCELLED, future, start=time(19, 0), released=True)
        expired = self._booking(Booking.Status.EXPIRED, future, start=time(20, 0), released=True)
        upcoming, past = partition_my_bookings(
            [failed, cancelled, expired],
            now=aware(self.today, 8),
        )
        self.assertEqual(upcoming, [])
        self.assertEqual(past, [failed, cancelled, expired])


class CodeAndQrTests(TestCase):
    def test_booking_code_format(self):
        self.assertRegex(generate_booking_code(), r"^MGZ-[A-Z0-9]{5}$")

    def test_qr_payload(self):
        self.assertEqual(
            qr_payload("MGZ-7F42K"),
            f"{settings.FRONTEND_URL.rstrip('/')}/pass/MGZ-7F42K",
        )
        self.assertIsNone(qr_payload(None))

    def test_grid_bounds(self):
        starts = list(iter_start_times())
        self.assertEqual(starts[0], time(8, 0))
        self.assertEqual(starts[-1], time(21, 0))
        self.assertEqual(end_time_for(time(21, 0)), time(22, 0))
