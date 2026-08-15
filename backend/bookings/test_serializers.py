from datetime import date, time

from django.test import TestCase

from accounts.models import User
from bookings.models import Booking, BookingSlot, Court
from bookings.serializers import (
    BookingStatusSerializer,
    CustomerBookingDetailSerializer,
    CustomerBookingListItemSerializer,
    CustomerBookingSerializer,
    PublicPassSerializer,
    StaffBookingListItemSerializer,
    StaffPassSerializer,
)
from bookings.seed import seed_courts

SLOT_DATE = date(2026, 8, 20)


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


class SerializerAudienceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone="01012345678",
            name="Ahmed Hassan",
            password="secret12",
        )
        seed_courts()
        self.court = Court.objects.get(slug="court-1")
        self.booking = Booking.objects.create(
            user=self.user,
            status=Booking.Status.CONFIRMED,
            booker_name=self.user.name,
            attendee_names=["Ahmed Hassan", "Omar Ali"],
            total_price_egp=700,
            total_price_cents=70000,
            booking_code="MGZ-7F42K",
            paymob_intention_id="pi_secret",
            paymob_transaction_id="txn-289187034",
        )
        BookingSlot.objects.create(
            booking=self.booking,
            court=self.court,
            date=SLOT_DATE,
            start_time=time(18, 0),
            price_egp=350,
            price_cents=35000,
        )
        BookingSlot.objects.create(
            booking=self.booking,
            court=self.court,
            date=SLOT_DATE,
            start_time=time(19, 0),
            price_egp=350,
            price_cents=35000,
        )

    def test_customer_omits_phone_and_paymob(self):
        data = CustomerBookingSerializer(self.booking).data
        self.assertFalse(has_sensitive_key(data))
        self.assertEqual(data["booking_code"], "MGZ-7F42K")
        self.assertEqual(len(data["slots"]), 2)
        self.assertEqual(data["slots"][0]["start_time"], "18:00")
        self.assertEqual(data["slots"][0]["end_time"], "19:00")
        self.assertEqual(data["slots"][1]["end_time"], "20:00")
        self.assertIn("/pass/MGZ-7F42K", data["qr_payload"])
        self.assertNotIn("paymob_intention_id", data)
        self.assertNotIn("paymob_transaction_id", data)

    def test_public_pass_omits_id_phone_and_paymob(self):
        data = PublicPassSerializer(self.booking).data
        self.assertFalse(has_sensitive_key(data))
        self.assertNotIn("id", data)
        self.assertEqual(
            set(data.keys()),
            {
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
            },
        )
        self.assertEqual(data["booking_code"], "MGZ-7F42K")
        self.assertEqual(data["booker_name"], "Ahmed Hassan")
        self.assertEqual(data["court"]["name"], "Court 1")
        self.assertEqual(data["date"], "2026-08-20")
        self.assertEqual(data["start_times"], ["18:00", "19:00"])
        self.assertEqual(data["start_time"], "18:00")
        self.assertEqual(data["end_time"], "20:00")
        self.assertEqual(data["price_egp"], 700)
        self.assertNotIn("slots", data)
        self.assertNotIn("price_cents", data)

    def test_status_poll_payload_is_minimal_and_gates_code(self):
        data = BookingStatusSerializer(self.booking).data
        self.assertEqual(
            set(data.keys()),
            {"id", "status", "booking_code", "pass_url", "hold_expires_at"},
        )
        self.assertEqual(data["booking_code"], "MGZ-7F42K")
        self.assertEqual(data["pass_url"], "/pass/MGZ-7F42K")
        self.assertFalse(has_sensitive_key(data))

        self.booking.status = Booking.Status.HELD
        held = BookingStatusSerializer(self.booking).data
        self.assertIsNone(held["booking_code"])
        self.assertIsNone(held["pass_url"])

    def test_detail_is_flattened_and_gates_code(self):
        data = CustomerBookingDetailSerializer(self.booking).data
        self.assertFalse(has_sensitive_key(data))
        self.assertEqual(data["booking_code"], "MGZ-7F42K")
        self.assertIn("/pass/MGZ-7F42K", data["qr_payload"])
        self.assertEqual(data["court"]["name"], "Court 1")
        self.assertEqual(data["start_times"], ["18:00", "19:00"])
        self.assertEqual(data["start_time"], "18:00")
        self.assertEqual(data["end_time"], "20:00")
        self.assertEqual(data["price_egp"], 700)
        self.assertNotIn("slots", data)
        self.assertNotIn("user", data)

        self.booking.status = Booking.Status.PENDING_PAYMENT
        pending = CustomerBookingDetailSerializer(self.booking).data
        self.assertIsNone(pending["booking_code"])
        self.assertIsNone(pending["qr_payload"])

    def test_staff_includes_phone_and_transaction_not_intention(self):
        data = StaffPassSerializer(self.booking).data
        self.assertEqual(data["booker_phone"], "01012345678")
        self.assertEqual(data["paymob_transaction_id"], "txn-289187034")
        self.assertNotIn("paymob_intention_id", data)
        self.assertFalse(data["can_redeem"])
        self.assertEqual(len(data["slots"]), 2)

    def test_staff_list_item_includes_all_child_slots(self):
        data = StaffBookingListItemSerializer(self.booking).data
        self.assertEqual(data["court_name"], "Court 1")
        self.assertEqual(data["start_time"], "18:00")
        self.assertEqual(data["end_time"], "20:00")
        self.assertEqual(len(data["slots"]), 2)
        self.assertEqual(data["slots"][0]["start_time"], "18:00")
        self.assertEqual(data["slots"][1]["start_time"], "19:00")
        self.assertEqual(data["booking_code"], "MGZ-7F42K")

    def test_list_item_uses_first_and_last_hours(self):
        data = CustomerBookingListItemSerializer(self.booking).data
        self.assertFalse(has_sensitive_key(data))
        self.assertEqual(data["court_name"], "Court 1")
        self.assertEqual(data["start_time"], "18:00")
        self.assertEqual(data["end_time"], "20:00")
        self.assertEqual(data["price_egp"], 700)
        self.assertEqual(data["period"], "evening")

    def test_list_item_hides_code_until_confirmed(self):
        self.booking.status = Booking.Status.HELD
        data = CustomerBookingListItemSerializer(self.booking).data
        self.assertIsNone(data["booking_code"])
