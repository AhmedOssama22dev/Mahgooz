from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

ACCESS_EXPIRES_IN = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())


def user_payload(user):
    return {
        "id": str(user.id),
        "name": user.name,
        "phone": user.phone,
    }


def issue_customer_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh["role"] = "customer"
    access = refresh.access_token
    access["role"] = "customer"
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
