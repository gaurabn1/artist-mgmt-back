from django.db import connection
from rest_framework import serializers

from apps.core.models import Artist, User, UserProfile
from apps.core.utils import convert_tuples_to_dicts


class UserRegistrationSerializer(serializers.Serializer):
    # Fields required for user creation
    role = serializers.ChoiceField(choices=User.Role.choices)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20)
    dob = serializers.DateField()
    gender = serializers.ChoiceField(choices=UserProfile.Gender.choices)
    address = serializers.CharField()
    is_active = serializers.BooleanField(required=False)

    # Artist-specific fields
    name = serializers.CharField(max_length=100, required=False)
    first_released_year = serializers.IntegerField(required=False, allow_null=True)
    no_of_album_released = serializers.IntegerField(
        required=False, allow_null=True, default=0
    )
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.ARTIST_MANAGER),
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        email = attrs.get("email", "")
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")
        return attrs

    def create(self, validated_data):
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO core_user
                (email, password, role, is_active, created_at, updated_at, is_staff, is_superuser)
                VALUES (%s, %s, %s, %s, NOW(), NOW(), FALSE, FALSE)
                RETURNING uuid, email, password, role, is_active
                """,
                [
                    validated_data.get("email", ""),
                    validated_data.get("password", ""),
                    validated_data.get("role", ""),
                    validated_data.get("is_active", False),
                ],
            )
            user = c.fetchone()
            user = convert_tuples_to_dicts(
                user,
                [
                    "uuid",
                    "email",
                    "password",
                    "role",
                    "is_active",
                ],
            )[0]
            print(user)
            return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
