from rest_framework import serializers

from bookings.models import Booking, Court
from bookings.policies import can_redeem, end_time_for, format_hhmm, price_for_start_time, qr_payload


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
    return [serialize_slot(slot) for slot in booking.slots.select_related("court").all()]


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


class PublicPassSerializer(serializers.ModelSerializer):
    slots = serializers.SerializerMethodField()
    qr_payload = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            "booking_code",
            "status",
            "booker_name",
            "attendee_names",
            "slots",
            "total_price_egp",
            "total_price_cents",
            "qr_payload",
            "redeemed_at",
        )

    def get_slots(self, booking):
        return _booking_slots(booking)

    def get_qr_payload(self, booking):
        return qr_payload(booking.booking_code)


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
        slots = list(booking.slots.all())
        if not slots:
            return None, None
        first = min(slots, key=lambda slot: (slot.date, slot.start_time))
        last = max(slots, key=lambda slot: (slot.date, slot.start_time))
        return first, last

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


class StaffBookingListItemSerializer(serializers.ModelSerializer):
    court_name = serializers.SerializerMethodField()
    start_time = serializers.SerializerMethodField()
    end_time = serializers.SerializerMethodField()

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
        )

    def _first_last(self, booking):
        slots = list(booking.slots.all())
        if not slots:
            return None, None
        first = min(slots, key=lambda slot: (slot.date, slot.start_time))
        last = max(slots, key=lambda slot: (slot.date, slot.start_time))
        return first, last

    def get_court_name(self, booking):
        first, _ = self._first_last(booking)
        return first.court.name if first else None

    def get_start_time(self, booking):
        first, _ = self._first_last(booking)
        return format_hhmm(first.start_time) if first else None

    def get_end_time(self, booking):
        _, last = self._first_last(booking)
        return format_hhmm(end_time_for(last.start_time)) if last else None
