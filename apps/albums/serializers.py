from django.db import connection
from rest_framework import serializers

from apps.core.models import Artist
from apps.core.utils import convert_tuples_to_dicts


class AlbumSerializer(serializers.Serializer):
    uuid = serializers.UUIDField(read_only=True)
    name = serializers.CharField(required=True)
    owner = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(), required=False
    )
    no_of_tracks = serializers.IntegerField(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    def to_representation(self, instance):
        return instance
