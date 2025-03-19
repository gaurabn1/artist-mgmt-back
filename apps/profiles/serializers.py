from django.db import connection
from rest_framework import serializers

from apps.core.models import UserProfile


class UserProfileSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    gender = serializers.ChoiceField(required=True, choices=UserProfile.Gender.choices)
    address = serializers.CharField(required=True)
    dob = serializers.DateField(required=True)
    is_active = serializers.BooleanField(required=False)

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)

    def create(self, validated_data):
        return UserProfile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE core_baseprofilemodel
                SET gender = %s, address = %s, dob = %s
                WHERE uuid = %s
                """,
                [
                    validated_data.get("gender", instance.get("gender", "")),
                    validated_data.get("address", instance.get("address", "")),
                    validated_data.get("dob", instance.get("dob", "")),
                    validated_data.get("uuid", instance.get("uuid", "")),
                ],
            )

            c.execute(
                """
                UPDATE profiles_userprofile
                SET first_name = %s, last_name = %s, phone = %s
                WHERE baseprofilemodel_ptr_id = %s
                """,
                [
                    validated_data.get("first_name", instance.get("first_name", "")),
                    validated_data.get("last_name", instance.get("last_name", "")),
                    validated_data.get("phone", instance.get("phone", "")),
                    validated_data.get("uuid", instance.get("uuid", "")),
                ],
            )

        return instance
