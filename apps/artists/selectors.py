from django.db import connection
from rest_framework import status
from rest_framework.response import Response

from apps.artists.serializers import ArtistSerializer
from apps.core.models import Artist
from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.selectors import ManagerSelector
from apps.users.utils import JWTManager, get_payload


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
        "manager_name",
    ]

    def __init__(self, headers):
        self.headers = headers

    def get_currect_artist(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if payload["role"] == "ARTIST":
            return ArtistSelector.get_artist_by_id(payload["user_id"])

        if payload["role"] == "ARTIST_MANAGER":
            return ManagerSelector.get_manager_by_id(payload["user_id"])
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get_artists_artist(self, user_id):
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
            print("A: ", artists)
        if artists is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        artists_dict = convert_tuples_to_dicts(artists, ArtistSelector.FIELD_NAMES)
        return Response(artists_dict, status=status.HTTP_200_OK)

    def get_artists(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        role = payload.get("role", "")
        user_id = payload.get("user_id", "")

        if role != "ARTIST_MANAGER" and role != "ARTIST":
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if role == "ARTIST":
            return self.get_artists_artist(user_id)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT uuid
                FROM profiles_userprofile
                WHERE user_id = %s
                """,
                [user_id],
            )

            manager = c.fetchone()
            if manager is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
            manager_dict = convert_tuples_to_dicts(manager, ["uuid"])[0]
            manager_id = manager_dict["uuid"]
            print(manager_id)

            c.execute(
                """
                SELECT
                a.uuid, a.name, a.first_released_year, a.no_of_album_released, a.dob, a.gender, a.address, u.is_active, u.email, a.manager_id as manager
                FROM artists_artist a
                JOIN core_user u ON a.user_id = u.uuid
                WHERE a.manager_id = %s
                """,
                [manager_id],
            )

            artists = c.fetchall()
        if artists is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        artists_dict = convert_tuples_to_dicts(artists, ArtistSelector.FIELD_NAMES)
        return Response(artists_dict, status=status.HTTP_200_OK)

    @staticmethod
    def get_artist_by_id(uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT
                a.uuid, a.name, a.first_released_year, a.no_of_album_released, a.dob, a.gender, a.address, u.is_active, u.email, a.manager_id as manager, m.first_name || ' ' || m.last_name as manager_name
                FROM artists_artist a
                JOIN core_user u ON a.user_id = u.uuid
                LEFT JOIN profiles_userprofile m ON a.manager_id = m.uuid
                WHERE a.uuid = %s
                """,
                [uuid],
            )
            artist = c.fetchone()
        if artist is None:
            return None
        artist = convert_tuples_to_dicts(artist, ArtistSelector.FIELD_NAMES)[0]
        serializer = ArtistSerializer(artist)
        return serializer.data
