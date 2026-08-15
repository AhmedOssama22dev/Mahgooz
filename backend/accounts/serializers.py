from rest_framework import serializers

from .phones import INVALID_PHONE_MESSAGE, InvalidPhone, normalize_phone


class PhoneField(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        try:
            return normalize_phone(value)
        except InvalidPhone:
            raise serializers.ValidationError(INVALID_PHONE_MESSAGE)


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=150)
    phone = PhoneField()
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)


class LoginSerializer(serializers.Serializer):
    phone = PhoneField()
    password = serializers.CharField(write_only=True)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
