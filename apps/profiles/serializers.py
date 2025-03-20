from datetime import datetime

from django.db import connection
from rest_framework import serializers

from apps.core.models import UserProfile
from apps.core.utils import convert_tuples_to_dicts


class UserProfileSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    gender = serializers.ChoiceField(required=True, choices=UserProfile.Gender.choices)
    address = serializers.CharField(required=True)
    dob = serializers.DateField(required=True)
    is_active = serializers.BooleanField(required=False)
    user_id = serializers.UUIDField(required=True)

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)

    def validate(self, attrs):
        dob = attrs.get("dob", "")
        current_date = datetime.now().date()

        if dob and dob > current_date:
            raise serializers.ValidationError("Date of birth cannot be in the future.")

        return attrs

    def create(self, validated_data):
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO profiles_userprofile
                (first_name, last_name, phone, gender, address, dob, created_at, updated_at, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                RETURNING uuid, first_name, last_name, phone, gender, address, dob, user_id
                """,
                [
                    validated_data.get("first_name", ""),
                    validated_data.get("last_name", ""),
                    validated_data.get("phone", ""),
                    validated_data.get("gender", ""),
                    validated_data.get("address", ""),
                    validated_data.get("dob", ""),
                    validated_data.get("user_id", None),
                ],
            )
            manager = c.fetchone()
        manager = convert_tuples_to_dicts(
            manager,
            [
                "uuid",
                "first_name",
                "last_name",
                "phone",
                "gender",
                "address",
                "dob",
                "user_id",
            ],
        )[0]
        return manager

    def update(self, instance, validated_data):
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE profiles_userprofile
                SET first_name = %s, last_name = %s, phone = %s, gender = %s, address = %s, dob = %s, updated_at = NOW()
                WHERE uuid = %s
                """,
                [
                    validated_data.get("first_name", instance.get("first_name", "")),
                    validated_data.get("last_name", instance.get("last_name", "")),
                    validated_data.get("phone", instance.get("phone", "")),
                    validated_data.get("gender", instance.get("gender", "")),
                    validated_data.get("address", instance.get("address", "")),
                    validated_data.get("dob", instance.get("dob", "")),
                    instance.get("uuid", ""),
                ],
            )

        return instance
