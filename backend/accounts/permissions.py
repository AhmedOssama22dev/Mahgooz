from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        token = getattr(request, "auth", None)
        if token is not None and hasattr(token, "get"):
            role = token.get("role")
            if role is not None and role != "customer":
                return False
        return True
