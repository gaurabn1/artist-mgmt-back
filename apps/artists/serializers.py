from datetime import datetime

from django.db import connection
from rest_framework import serializers

from apps.core.models import Artist, User
from apps.core.utils import convert_tuples_to_dicts


class ArtistSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField()
    user_id = serializers.UUIDField(read_only=True, required=False)
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.ARTIST_MANAGER),
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

        if dob and dob > current_date:
            raise serializers.ValidationError("Date of birth cannot be in the future.")

        if first_released_year and first_released_year > current_date.year:
            raise serializers.ValidationError(
                "First released year cannot be in the future."
            )

        if first_released_year and dob.year > first_released_year:
            raise serializers.ValidationError(
                "Date of birth cannot be greater than first released year."
            )

        return attrs
