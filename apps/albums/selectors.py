from django.db import connection

from apps.albums.serializers import AlbumSerializer
from apps.core.utils import convert_tuples_to_dicts
from apps.users.utils import JWTManager


class AlbumSelector:
    FIELD_NAMES = [
        "uuid",
        "name",
        "owner_id",
        "no_of_tracks",
        "image",
        "owner",
    ]

    @staticmethod
    def get_albums(headers):
        with connection.cursor() as c:
            user_payload = JWTManager.decode_jwt_token(
                headers.get("Authorization", "").split(" ")[1]
            )
            if user_payload is not None and user_payload.get("role", "") == "ARTIST":
                user_id = user_payload.get("user_id", "")
                c.execute(
                    """
                    SELECT uuid
                    FROM artists_artist
                    WHERE user_id = %s
                    """,
                    [user_id],
                )
                artist = c.fetchone()
                artist_dict = convert_tuples_to_dicts(artist, ["uuid"])[0]

                if artist_dict is None:
                    return None
                user_id = artist_dict["uuid"]

                c.execute(
                    """
                    SELECT  a.uuid, a.name, a.owner_id, a.no_of_tracks, a.image, b.name as owner
                    FROM albums_album a
                    JOIN artists_artist b ON a.owner_id = b.uuid
                    WHERE a.owner_id = %s
                    """,
                    [user_id],
                )
                albums = c.fetchall()
                if albums is None:
                    return None
            else:
                c.execute(
                    """
                    SELECT  a.uuid, a.name, a.owner_id, a.no_of_tracks, a.image, b.name as owner
                    FROM albums_album a
                    JOIN artists_artist b ON a.owner_id = b.uuid
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
