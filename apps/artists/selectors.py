from datetime import timedelta

from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.artists.serializers import ArtistSerializer
from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.selectors import ManagerSelector
from apps.users.utils import get_payload


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

    def get_artists_count(self):
        time_15_minutes_ago = timezone.now() - timedelta(minutes=15)
        with connection.cursor() as c:
            c.execute(
                """
            SELECT
                (SELECT count(*) FROM artists_artist),
                (SELECT count(*) FROM artists_artist WHERE created_at > %s);
            """,
                [time_15_minutes_ago],
            )
            artist_result = c.fetchone()
            c.execute(
                """
            SELECT
                (SELECT count(*) FROM albums_album),
                (SELECT count(*) FROM albums_album WHERE created_at > %s);
                """,
                [time_15_minutes_ago],
            )
            album_result = c.fetchone()
            c.execute(
                """
            SELECT
                (SELECT count(*) FROM musics_music),
                (SELECT count(*) FROM musics_music WHERE created_at > %s);
                """,
                [time_15_minutes_ago],
            )
            music_result = c.fetchone()
        if artist_result is None or album_result is None or music_result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "artist_count": artist_result[0],
                "artists_last_15_minutes": artist_result[1],
                "album_count": album_result[0],
                "albums_last_15_minutes": album_result[1],
                "music_count": music_result[0],
                "musics_last_15_minutes": music_result[1],
            },
            status=status.HTTP_200_OK,
        )

    def get_currect_artist(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT uuid
                FROM artists_artist
                WHERE user_id = %s
                """,
                [payload["user_id"]],
            )
            artist = c.fetchone()
            if artist is None:
                return Response(
                    {"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND
                )
        artist_dict = convert_tuples_to_dicts(artist, ["uuid"])[0]
        if payload["role"] == "ARTIST":
            return self.get_artist_by_id(artist_dict["uuid"])

        if payload["role"] == "ARTIST_MANAGER":
            return ManagerSelector.get_manager_by_id(payload["user_id"])
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    def get_artists_artist(self):
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
        if artists is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        artists_dict = convert_tuples_to_dicts(artists, self.FIELD_NAMES)
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
            return self.get_artists_artist()  # Get all artists

        # If role is an artist manager
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
        artists_dict = convert_tuples_to_dicts(artists, self.FIELD_NAMES)
        return Response(artists_dict, status=status.HTTP_200_OK)

    def get_artist_by_id(self, uuid):
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
            print("A: ", artist)
        if artist is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        artist = convert_tuples_to_dicts(artist, self.FIELD_NAMES)[0]
        serializer = ArtistSerializer(artist)
        return Response(serializer.data, status=status.HTTP_200_OK)
