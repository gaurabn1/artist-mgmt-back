from datetime import datetime

from django.db import connection
from rest_framework import serializers

from apps.core.models import Artist, User
from apps.core.utils import convert_tuples_to_dicts


class ArtistSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(required=True)
    user_id = serializers.UUIDField(required=True)
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.ARTIST_MANAGER),
        required=False,
        allow_null=True,
    )
    manager_name = serializers.CharField(read_only=True)
    first_released_year = serializers.IntegerField(required=True)
    no_of_album_released = serializers.IntegerField(required=False, default=0)
    dob = serializers.DateField(required=True)
    gender = serializers.ChoiceField(required=True, choices=Artist.Gender.choices)
    address = serializers.CharField(required=True)
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

    def create(self, validated_data):
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO artists_artist
                (name, first_released_year, no_of_album_released, dob, gender, address, manager_id, created_at, updated_at, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                RETURNING uuid, name, first_released_year, no_of_album_released, dob, gender, address, manager_id, user_id
                """,
                [
                    validated_data.get("name", ""),
                    validated_data.get("first_released_year", ""),
                    validated_data.get("no_of_album_released", 0),
                    validated_data.get("dob", ""),
                    validated_data.get("gender", ""),
                    validated_data.get("address", ""),
                    validated_data.get("manager", None),
                    validated_data.get("user_id", None),
                ],
            )
            artist = c.fetchone()
            artist = convert_tuples_to_dicts(
                artist,
                [
                    "uuid",
                    "name",
                    "first_released_year",
                    "no_of_album_released",
                    "dob",
                    "gender",
                    "address",
                    "manager_id",
                    "user_id",
                ],
            )[0]
            return artist
