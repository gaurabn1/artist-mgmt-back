from rest_framework import serializers

from apps.artists.serializers import ArtistSerializer
from apps.core.models import Album, Artist, Music


class MusicSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    genre = serializers.ChoiceField(required=True, choices=Music.Genre.choices)
    album = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(), required=False
    )
    artist = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(), required=True
    )

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)
