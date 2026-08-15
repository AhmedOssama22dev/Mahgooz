from django.contrib.auth import authenticate
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from config.exceptions import APIError

from .models import User
from .permissions import IsCustomer
from .serializers import LoginSerializer, RefreshSerializer, RegisterSerializer
from .tokens import access_token_payload, issue_customer_tokens, user_payload


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if User.objects.filter(phone=data["phone"]).exists():
            raise APIError(
                "PHONE_TAKEN",
                "An account with this phone already exists.",
                status.HTTP_409_CONFLICT,
            )
        try:
            user = User.objects.create_user(
                phone=data["phone"],
                name=data["name"],
                password=data["password"],
            )
        except IntegrityError:
            raise APIError(
                "PHONE_TAKEN",
                "An account with this phone already exists.",
                status.HTTP_409_CONFLICT,
            )
        return Response(issue_customer_tokens(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            phone=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            raise APIError(
                "INVALID_CREDENTIALS",
                "Phone or password is incorrect.",
                status.HTTP_401_UNAUTHORIZED,
            )
        return Response(issue_customer_tokens(user))


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh = RefreshToken(serializer.validated_data["refresh"])
            access = refresh.access_token
            access["role"] = refresh.get("role", "customer")
        except (TokenError, InvalidToken):
            raise APIError(
                "UNAUTHENTICATED",
                "Refresh token is invalid or expired.",
                status.HTTP_401_UNAUTHORIZED,
            )
        return Response(access_token_payload(access))


class MeView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        return Response(user_payload(request.user))
