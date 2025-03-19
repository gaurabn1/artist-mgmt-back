from django.db import connection

from apps.artists.serializers import ArtistSerializer
from apps.core.models import Artist
from apps.core.utils import convert_tuples_to_dicts


class ArtistSelector:
    FIELD_NAMES = [
        "uuid",
        "name",
        "first_released_year",
        "no_of_album_released",
        "dob",
        "gender",
        "address",
        "is_active",
        "email",
        "manager",
    ]

    @staticmethod
    def get_artists():
        with connection.cursor() as c:
            c.execute(
                """
                SELECT
                a.uuid, a.name, a.first_released_year, a.no_of_album_released, a.dob, a.gender, a.address, u.is_active, u.email, a.manager_id as manager
                FROM artists_artist a
                JOIN core_user u ON a.user_id = u.uuid
                """
            )

            artists = c.fetchall()

        artists = convert_tuples_to_dicts(artists, ArtistSelector.FIELD_NAMES)
        if artists is None:
            return None
        serializer = ArtistSerializer(artists, many=True)
        return serializer.data

    @staticmethod
    def get_artist_by_id(uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT
                a.uuid, a.name, a.first_released_year, a.no_of_album_released, a.dob, a.gender, a.address, u.is_active, u.email, a.manager_id as manager
                FROM artists_artist a
                JOIN core_user u ON a.user_id = u.uuid
                WHERE a.uuid = %s
                """,
                [uuid],
            )
            artist = c.fetchone()
        artist = convert_tuples_to_dicts(artist, ArtistSelector.FIELD_NAMES)[0]
        if artist is None:
            return None
        serializer = ArtistSerializer(artist)
        return serializer.data
