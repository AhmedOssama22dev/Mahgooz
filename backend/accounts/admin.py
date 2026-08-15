from django.contrib import admin

from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone", "name", "is_staff", "is_active")
    search_fields = ("phone", "name")
    ordering = ("phone",)
    readonly_fields = ("id", "date_joined", "last_login")
