from datetime import datetime

from django.db import connection
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.core.models import Artist, User, UserProfile
from apps.core.utils import convert_tuples_to_dicts


class ArtistSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    user_id = serializers.UUIDField(read_only=True, required=False)
    manager = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all(),
        required=False,
        allow_null=True,
    )
    manager_name = serializers.CharField(read_only=True)
    first_released_year = serializers.IntegerField(required=False, allow_null=True)
    no_of_album_released = serializers.IntegerField(required=False, default=0)
    dob = serializers.DateField()
    gender = serializers.ChoiceField(choices=Artist.Gender.choices)
    address = serializers.CharField()
    is_active = serializers.BooleanField(required=False)

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)

    def validate(self, attrs):
        dob = attrs.get("dob", "")
        first_released_year = attrs.get("first_released_year", "")
        current_date = datetime.now().date()

        if isinstance(dob, str):
            try:
                dob = datetime.strptime(dob, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError(
                    "Invalid date format for date of birth. Use YYYY-MM-DD."
                )

        if first_released_year and first_released_year > current_date.year:
            raise serializers.ValidationError(
                "First released year cannot be in the future."
            )

        if first_released_year and dob and dob.year > first_released_year:
            raise ValidationError(
                "Date of birth cannot be greater than first released year."
            )

        return attrs

    def validate_dob(self, value):
        current_date = datetime.now().date()
        return (
            value
            if value <= current_date
            else ValidationError("Date of birth cannot be in the future.")
        )

    def validate_no_of_album_released(self, value):
        return value if value is not None else 0

    def validate_first_released_year(self, value):
        return value if value is not None else 0
