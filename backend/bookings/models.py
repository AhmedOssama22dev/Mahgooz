import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


def validate_attendee_names(value):
    if not isinstance(value, list) or not (1 <= len(value) <= 4):
        raise ValidationError("Enter between 1 and 4 attendee names.")
    if any(not isinstance(name, str) or not name.strip() for name in value):
        raise ValidationError("Each attendee name must be a non-empty string.")


class Court(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class Booking(models.Model):
    class Status(models.TextChoices):
        HELD = "held", "Held"
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        CONFIRMED = "confirmed", "Confirmed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"
        REDEEMED = "redeemed", "Redeemed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.HELD,
    )
    booker_name = models.CharField(max_length=150)
    attendee_names = models.JSONField(validators=[validate_attendee_names])
    total_price_egp = models.PositiveIntegerField()
    total_price_cents = models.PositiveIntegerField()
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    booking_code = models.CharField(max_length=16, unique=True, null=True, blank=True)
    paymob_intention_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    paymob_transaction_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.booking_code or str(self.id)


class BookingSlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    court = models.ForeignKey(
        Court,
        on_delete=models.PROTECT,
        related_name="slots",
    )
    date = models.DateField()
    start_time = models.TimeField()
    price_egp = models.PositiveIntegerField()
    price_cents = models.PositiveIntegerField()
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "date", "start_time"],
                name="uniq_booking_slot_start",
            ),
            models.UniqueConstraint(
                fields=["court", "date", "start_time"],
                condition=Q(released_at__isnull=True),
                name="uniq_active_court_slot",
            ),
        ]

    def __str__(self):
        return f"{self.court} {self.date} {self.start_time}"
