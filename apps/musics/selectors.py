from django.db import connection
from rest_framework import status
from rest_framework.response import Response

from apps.core.utils import convert_tuples_to_dicts
from apps.musics.serializers import MusicSerializer
from apps.users.utils import get_payload


class MusicSelector:
    FIELD_NAMES = [
        "uuid",
        "title",
        "album_id",
        "genre",
        "artist_uuid",
        "artist_name",
        "album_uuid",
        "album_name",
    ]

    def __init__(self, headers):
        self.headers = headers

    def get_music_artist(self, user_id):
        with connection.cursor() as c:
            c.execute(
                """
                    SELECT m.uuid, m.title, m.album_id, m.genre, ar.uuid as artist_uuid, ar.name as artist_name, a.uuid as album_uuid, a.name as album_name
                    FROM musics_music m
                    LEFT JOIN albums_album a ON m.album_id = a.uuid
                    LEFT JOIN artists_artist ar ON m.artist_id = ar.uuid
                    WHERE ar.user_id = %s
                    """,
                [user_id],
            )
            musics = c.fetchall()
            if musics is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
        musics_dict = convert_tuples_to_dicts(musics, self.FIELD_NAMES)
        for music in musics_dict:
            music["artist"] = {
                "uuid": music.pop("artist_uuid"),
                "name": music.pop("artist_name"),
            }
            music["album"] = {
                "uuid": music.pop("album_uuid"),
                "name": music.pop("album_name"),
            }
        serializer = MusicSerializer(musics_dict, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_music_manager(self, user_id):
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
                return Response(
                    {"detail": "Manager not found"}, status=status.HTTP_404_NOT_FOUND
                )
            manager_dict = convert_tuples_to_dicts(manager, ["uuid"])[0]
            manager_id = manager_dict["uuid"]

            c.execute(
                """
                SELECT m.uuid, m.title, m.album_id, m.genre, ar.uuid as artist_uuid, ar.name as artist_name, a.uuid as album_uuid, a.name as album_name
                FROM musics_music m
                LEFT JOIN albums_album a ON m.album_id = a.uuid
                LEFT JOIN artists_artist ar ON m.artist_id = ar.uuid
                WHERE ar.manager_id = %s
                """,
                [manager_id],
            )
            musics = c.fetchall()
        if musics is None:
            return Response(
                {"detail": "Musics not found"}, status=status.HTTP_404_NOT_FOUND
            )

        musics_dict = convert_tuples_to_dicts(musics, MusicSelector.FIELD_NAMES)
        for music in musics_dict:
            music["artist"] = {
                "uuid": music.pop("artist_uuid"),
                "name": music.pop("artist_name"),
            }
            if music["album_id"] is not None:
                music.pop("album_id")
                music["album"] = {
                    "uuid": music.pop("album_uuid"),
                    "name": music.pop("album_name"),
                }
        serializer = MusicSerializer(musics_dict, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_musics(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_role = payload.get("role", "")
        user_id = payload.get("user_id", "")

        if user_role != "ARTIST" and user_role != "ARTIST_MANAGER":
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if user_role == "ARTIST":
            return self.get_music_artist(user_id)

        if user_role == "ARTIST_MANAGER":
            return self.get_music_manager(user_id)

    def get_music_by_id(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT uuid, title, album_id, genre, artist_id
                FROM musics_music
                WHERE uuid = %s
                """,
                [uuid],
            )
            music = c.fetchone()
        if music is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        music_dict = convert_tuples_to_dicts(music, MusicSelector.FIELD_NAMES)[0]
        serializer = MusicSerializer(music_dict)
        return Response(serializer.data, status=status.HTTP_200_OK)
