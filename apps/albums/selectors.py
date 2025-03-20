from django.db import connection

from apps.albums.serializers import AlbumSerializer
from apps.core.utils import convert_tuples_to_dicts


class AlbumSelector:
    FIELD_NAMES = [
        "uuid",
        "name",
        "owner",
        "no_of_tracks",
        "image",
    ]

    @staticmethod
    def get_albums():
        with connection.cursor() as c:
            c.execute(
                """
                SELECT  uuid, name, owner_id, no_of_tracks, image
                FROM albums_album;
                """
            )
            albums = c.fetchall()
            if albums is None:
                return None
        albums = convert_tuples_to_dicts(albums, AlbumSelector.FIELD_NAMES)
        serializer = AlbumSerializer(albums, many=True)
        return serializer.data

    @staticmethod
    def get_album_by_id(uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT  uuid, name, owner_id, no_of_tracks, image
                FROM albums_album
                WHERE uuid = %s
                """,
                [uuid],
            )
            album = c.fetchone()
        if album is None:
            return None
        album = convert_tuples_to_dicts(album, AlbumSelector.FIELD_NAMES)[0]
        serializer = AlbumSerializer(album)
        return serializer.data
