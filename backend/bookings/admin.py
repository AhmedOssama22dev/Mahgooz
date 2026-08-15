from django.contrib import admin

from .models import Booking, BookingSlot, Court


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    ordering = ("sort_order", "name")
    search_fields = ("name", "slug")
    readonly_fields = ("id",)


class BookingSlotInline(admin.TabularInline):
    model = BookingSlot
    extra = 0
    readonly_fields = ("id",)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking_code",
        "status",
        "booker_name",
        "total_price_egp",
        "hold_expires_at",
    )
    list_filter = ("status",)
    search_fields = ("booking_code", "booker_name")
    readonly_fields = ("id", "created_at", "updated_at")
    inlines = [BookingSlotInline]


@admin.register(BookingSlot)
class BookingSlotAdmin(admin.ModelAdmin):
    list_display = ("booking", "court", "date", "start_time", "price_egp", "released_at")
    list_filter = ("court", "date")
    readonly_fields = ("id",)
