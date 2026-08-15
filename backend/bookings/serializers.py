from rest_framework import serializers

from bookings.models import Booking, Court
from bookings.policies import (
    booking_slots_list,
    can_redeem,
    end_time_for,
    first_last_slots,
    format_hhmm,
    issued_booking_code,
    pass_url,
    price_for_start_time,
    qr_payload,
)


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = ("id", "name", "slug")


class CourtSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class SlotSerializer(serializers.Serializer):
    court = CourtSummarySerializer()
    date = serializers.DateField()
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    period = serializers.CharField()
    price_egp = serializers.IntegerField()
    price_cents = serializers.IntegerField()


class HoldSlotInputSerializer(serializers.Serializer):
    court_id = serializers.UUIDField()
    date = serializers.DateField()
    start_time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])


class HoldRequestSerializer(serializers.Serializer):
    slots = HoldSlotInputSerializer(many=True, allow_empty=False)
    attendee_names = serializers.ListField(
        child=serializers.CharField(max_length=150),
        min_length=1,
        max_length=4,
    )

    def validate_attendee_names(self, value):
        cleaned = []
        for name in value:
            stripped = name.strip()
            if not stripped:
                raise serializers.ValidationError("Each attendee name must be a non-empty string.")
            cleaned.append(stripped)
        return cleaned


class SlotGridItemSerializer(serializers.Serializer):
    start_time = serializers.CharField()
    end_time = serializers.CharField()
    state = serializers.CharField()
    period = serializers.CharField()
    price_egp = serializers.IntegerField()
    price_cents = serializers.IntegerField()
    label = serializers.CharField(allow_null=True, allow_blank=True)


class OperatingHoursSerializer(serializers.Serializer):
    open = serializers.CharField()
    close = serializers.CharField()


class SlotGridSerializer(serializers.Serializer):
    date = serializers.DateField()
    court = CourtSummarySerializer()
    operating_hours = OperatingHoursSerializer()
    slot_minutes = serializers.IntegerField()
    slots = SlotGridItemSerializer(many=True)


class SlotQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
    court_id = serializers.UUIDField()


class StaffDateQuerySerializer(serializers.Serializer):
    date = serializers.DateField(required=False)


def serialize_slot(slot):
    pricing = price_for_start_time(slot.start_time)
    return {
        "court": {"id": slot.court_id, "name": slot.court.name},
        "date": slot.date,
        "start_time": format_hhmm(slot.start_time),
        "end_time": format_hhmm(end_time_for(slot.start_time)),
        "period": pricing["period"],
        "price_egp": slot.price_egp,
        "price_cents": slot.price_cents,
    }


def _booking_slots(booking):
    return [serialize_slot(slot) for slot in booking_slots_list(booking)]


class BookingScheduleMixin:
    def _first_last(self, booking):
        return first_last_slots(booking)

    def get_court(self, booking):
        first, _ = self._first_last(booking)
        if first is None:
            return None
        return {"id": str(first.court_id), "name": first.court.name}

    def get_date(self, booking):
        first, _ = self._first_last(booking)
        return first.date.isoformat() if first else None

    def get_start_times(self, booking):
        return [format_hhmm(slot.start_time) for slot in booking_slots_list(booking)]

    def get_start_time(self, booking):
        first, _ = self._first_last(booking)
        return format_hhmm(first.start_time) if first else None

    def get_end_time(self, booking):
        _, last = self._first_last(booking)
        return format_hhmm(end_time_for(last.start_time)) if last else None

    def get_booking_code(self, booking):
        return issued_booking_code(booking)

    def get_qr_payload(self, booking):
        return qr_payload(issued_booking_code(booking))


class CustomerBookingSerializer(serializers.ModelSerializer):
    slots = serializers.SerializerMethodField()
    qr_payload = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            "id",
            "status",
            "booker_name",
            "attendee_names",
            "slots",
            "total_price_egp",
            "total_price_cents",
            "hold_expires_at",
            "booking_code",
            "qr_payload",
            "redeemed_at",
            "created_at",
        )

    def get_slots(self, booking):
        return _booking_slots(booking)

    def get_qr_payload(self, booking):
        return qr_payload(booking.booking_code)


class BookingStatusSerializer(serializers.ModelSerializer):
    booking_code = serializers.SerializerMethodField()
    pass_url = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = ("id", "status", "booking_code", "pass_url", "hold_expires_at")

    def get_booking_code(self, booking):
        return issued_booking_code(booking)

    def get_pass_url(self, booking):
        return pass_url(issued_booking_code(booking))


class CustomerBookingDetailSerializer(BookingScheduleMixin, serializers.ModelSerializer):
    court = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    start_times = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    booking_code = serializers.SerializerMethodField()
    qr_payload = serializers.SerializerMethodField()
    price_egp = serializers.IntegerField(source="total_price_egp")
    price_cents = serializers.IntegerField(source="total_price_cents")

    class Meta:
        model = Booking
        fields = (
            "id",
            "status",
            "court",
            "date",
            "start_times",
            "start_time",
            "end_time",
            "booker_name",
            "attendee_names",
            "price_egp",
            "price_cents",
            "hold_expires_at",
            "booking_code",
            "qr_payload",
            "redeemed_at",
            "created_at",
        )


class PublicPassSerializer(BookingScheduleMixin, serializers.ModelSerializer):
    court = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    start_times = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    booking_code = serializers.SerializerMethodField()
    qr_payload = serializers.SerializerMethodField()
    price_egp = serializers.IntegerField(source="total_price_egp")

    class Meta:
        model = Booking
        fields = (
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
        )


class StaffPassSerializer(serializers.ModelSerializer):
    slots = serializers.SerializerMethodField()
    booker_phone = serializers.SerializerMethodField()
    can_redeem = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            "booking_code",
            "status",
            "can_redeem",
            "booker_name",
            "booker_phone",
            "attendee_names",
            "slots",
            "total_price_egp",
            "total_price_cents",
            "paymob_transaction_id",
            "redeemed_at",
        )

    def get_slots(self, booking):
        return _booking_slots(booking)

    def get_booker_phone(self, booking):
        return booking.user.phone

    def get_can_redeem(self, booking):
        return can_redeem(booking)


class CustomerBookingListItemSerializer(serializers.ModelSerializer):
    court_name = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    period = serializers.SerializerMethodField()
    booking_code = serializers.SerializerMethodField()
    price_egp = serializers.IntegerField(source="total_price_egp")

    class Meta:
        model = Booking
        fields = (
            "id",
            "status",
            "court_name",
            "date",
            "start_time",
            "end_time",
            "price_egp",
            "booking_code",
            "period",
        )

    def _first_last(self, booking):
        return first_last_slots(booking)

    def get_court_name(self, booking):
        first, _ = self._first_last(booking)
        return first.court.name if first else None

    def get_date(self, booking):
        first, _ = self._first_last(booking)
        return first.date.isoformat() if first else None

    def get_start_time(self, booking):
        first, _ = self._first_last(booking)
        return format_hhmm(first.start_time) if first else None

    def get_end_time(self, booking):
        _, last = self._first_last(booking)
        return format_hhmm(end_time_for(last.start_time)) if last else None

    def get_period(self, booking):
        first, _ = self._first_last(booking)
        if first is None:
            return None
        return price_for_start_time(first.start_time)["period"]

    def get_booking_code(self, booking):
        return issued_booking_code(booking)


class StaffBookingListItemSerializer(serializers.ModelSerializer):
    court_name = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()
    slots = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            "booking_code",
            "status",
            "court_name",
            "start_time",
            "end_time",
            "booker_name",
            "redeemed_at",
            "slots",
        )

    def _first_last(self, booking):
        return first_last_slots(booking)

    def get_court_name(self, booking):
        first, _ = self._first_last(booking)
        return first.court.name if first else None

    def get_start_time(self, booking):
        first, _ = self._first_last(booking)
        return format_hhmm(first.start_time) if first else None

    def get_end_time(self, booking):
        _, last = self._first_last(booking)
        return format_hhmm(end_time_for(last.start_time)) if last else None

    def get_slots(self, booking):
        return _booking_slots(booking)
