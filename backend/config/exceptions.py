from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def envelope(code, message, details=None):
    payload = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


class APIError(APIException):
    def __init__(self, code, message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
        self.status_code = status_code
        self.default_code = code
        self.default_detail = message
        super().__init__(detail=message, code=code)
        self.error_code = code
        self.error_message = message
        self.error_details = details


def _as_details(data):
    if isinstance(data, dict):
        return {key: _as_details(value) for key, value in data.items()}
    if isinstance(data, list):
        return [_as_details(item) for item in data]
    return str(data)


def api_exception_handler(exc, context):
    if isinstance(exc, APIError):
        return Response(
            envelope(exc.error_code, exc.error_message, exc.error_details),
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        return Response(
            envelope("INTERNAL_ERROR", "Unexpected server error"),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, ValidationError):
        return Response(
            envelope("VALIDATION_ERROR", "Invalid request body", _as_details(response.data)),
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, NotAuthenticated):
        return Response(
            envelope("UNAUTHENTICATED", "Authentication credentials were not provided."),
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, AuthenticationFailed):
        return Response(
            envelope("UNAUTHENTICATED", "Authentication credentials were not provided."),
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, PermissionDenied):
        message = str(exc.detail) if exc.detail else "You do not have permission to perform this action."
        return Response(envelope("FORBIDDEN", message), status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, NotFound):
        message = str(exc.detail) if exc.detail else "Not found."
        return Response(envelope("NOT_FOUND", message), status=status.HTTP_404_NOT_FOUND)

    data = response.data
    if response.status_code >= 500:
        return Response(
            envelope("INTERNAL_ERROR", "Unexpected server error"),
            status=response.status_code,
        )
    if isinstance(data, dict) and "detail" in data:
        message = str(data["detail"])
    else:
        message = "Unexpected error"
    return Response(envelope("ERROR", message), status=response.status_code)
