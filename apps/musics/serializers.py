from rest_framework import serializers

from apps.albums.serializers import AlbumSerializer
from apps.artists.serializers import ArtistSerializer
from apps.core.models import Album, Artist, Music


class MusicSerializer(serializers.Serializer):
    title = serializers.CharField(required=True)
    genre = serializers.ChoiceField(required=True, choices=Music.Genre.choices)
    album_id = serializers.PrimaryKeyRelatedField(
        queryset=Album.objects.all(), required=False
    )
    album = AlbumSerializer(read_only=True)
    artist = ArtistSerializer(read_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=Artist.objects.all(), required=False
    )

    def to_representation(self, instance):
        if isinstance(instance, dict):
            return instance
        return super().to_representation(instance)
