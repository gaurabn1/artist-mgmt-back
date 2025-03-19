from django.db import connection

from apps.artists.selectors import ArtistSelector
from apps.artists.serializers import ArtistSerializer


class ArtistService:

    @staticmethod
    def update_artist(uuid, data):
        artist = ArtistSelector.get_artist_by_id(uuid)
        if artist is None:
            return None
        if data.get("is_active") is not None or data.get("email") is not None:
            new_email = data.pop("email", artist.get("email", ""))
            is_active = data.pop("is_active", artist.get("is_active", False))
            with connection.cursor() as c:
                c.execute(
                    """
                UPDATE core_user
                SET is_active = %s
                WHERE email = %s
                """,
                    [is_active, artist.get("email", None)],
                )

                c.execute(
                    """
                    UPDATE core_user
                    SET email = %s
                    WHERE email = %s
                    """,
                    [new_email, artist.get("email", None)],
                )
        serializer = ArtistSerializer(artist, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data

    @staticmethod
    def delete_artist(uuid):
        artist = ArtistSelector.get_artist_by_id(uuid)
        if artist is None:
            return None
        with connection.cursor() as c:
            c.execute("DELETE FROM artists_artist WHERE uuid = %s;", [uuid])
            c.execute(
                "DELETE FROM core_user WHERE email = %s;", [artist.get("email", "")]
            )

        return True
