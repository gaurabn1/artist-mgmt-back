from django.db import connection

from apps.artists.selectors import ArtistSelector
from apps.artists.serializers import ArtistSerializer
from apps.core.utils import convert_tuples_to_dicts


class ArtistService:

    @staticmethod
    def serialize_data(data):
        serializer = ArtistSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer

    @staticmethod
    def update_artist(uuid, data):
        ArtistService.serialize_data(data)
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
                SET is_active = %s, email = %s, updated_at = NOW()
                WHERE email = %s
                """,
                    [is_active, new_email, artist.get("email", None)],
                )

        with connection.cursor() as c:
            c.execute(
                """
                UPDATE artists_artist
                SET name = %s, first_released_year = %s, no_of_album_released = %s, dob = %s, gender = %s, address = %s, manager_id = %s, updated_at = NOW()
                WHERE uuid = %s
                RETURNING uuid, name, first_released_year, no_of_album_released, dob, gender, address, manager_id
                """,
                [
                    data.get("name", artist.get("name", "")),
                    data.get(
                        "first_released_year", artist.get("first_released_year", "")
                    ),
                    data.get(
                        "no_of_album_released", artist.get("no_of_album_released", 0)
                    ),
                    data.get("dob", artist.get("dob", "")),
                    data.get("gender", artist.get("gender", "")),
                    data.get("address", artist.get("address", "")),
                    data.get("manager", artist.get("manager", None)),
                    uuid,
                ],
            )
            artist = c.fetchone()
        artist_dict = convert_tuples_to_dicts(
            artist,
            [
                "uuid",
                "name",
                "first_released_year",
                "no_of_album_released",
                "dob",
                "gender",
                "address",
                "manager",
            ],
        )[0]
        if artist_dict is None:
            return None

        serializer = ArtistSerializer(artist_dict)
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
