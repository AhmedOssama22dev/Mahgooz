from rest_framework_simplejwt.authentication import JWTAuthentication


class StaffPrincipal:
    is_authenticated = True
    is_anonymous = False
    is_active = True
    is_staff = True
    is_superuser = False
    pk = None
    id = None
    phone = None
    name = "Staff"

    def __str__(self):
        return "staff"


class RoleJWTAuthentication(JWTAuthentication):
    """Customer tokens load the user; staff PIN tokens have no user row."""

    def get_user(self, validated_token):
        if validated_token.get("role") == "staff":
            return StaffPrincipal()
        return super().get_user(validated_token)
