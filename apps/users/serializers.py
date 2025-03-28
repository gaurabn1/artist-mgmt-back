from rest_framework import serializers

from apps.core.models import User


class UserRegistrationSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.Role.choices)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email", "")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return attrs


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
