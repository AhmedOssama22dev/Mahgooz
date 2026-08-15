from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Any logged-in account may book — staff share the same login."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsStaff(BasePermission):
    message = "Staff token required."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "is_staff", False))
