from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

ACCESS_EXPIRES_IN = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())


def role_for(user):
    return "staff" if getattr(user, "is_staff", False) else "customer"


def user_payload(user):
    return {
        "id": str(user.id),
        "name": user.name,
        "phone": user.phone,
        "role": role_for(user),
    }


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    role = role_for(user)
    refresh["role"] = role
    access = refresh.access_token
    access["role"] = role
    return {
        "access": str(access),
        "refresh": str(refresh),
        "token_type": "Bearer",
        "expires_in": ACCESS_EXPIRES_IN,
        "user": user_payload(user),
    }


def access_token_payload(access):
    return {
        "access": str(access),
        "token_type": "Bearer",
        "expires_in": ACCESS_EXPIRES_IN,
    }
