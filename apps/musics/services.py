from django.db import connection
from rest_framework import status
from rest_framework.response import Response

from apps.core.utils import convert_tuples_to_dicts
from apps.musics.serializers import MusicSerializer
from apps.users.utils import get_payload


class MusicService:

    def __init__(self, data, headers):
        self.data = data
        self.headers = headers

    def update_album_and_artist_counts(self, album_id, artist_id):
        with connection.cursor() as cursor:
            # Update album's track count after music change
            cursor.execute(
                """
                UPDATE albums_album
                SET no_of_tracks = (SELECT COUNT(*) FROM musics_music WHERE album_id = %s)
                WHERE uuid = %s
            """,
                [album_id, album_id],
            )

            # Update artist's album count
            cursor.execute(
                """
                UPDATE artists_artist
                SET no_of_album_released = (SELECT COUNT(*) FROM albums_album WHERE owner_id = %s)
                WHERE uuid = %s
            """,
                [artist_id, artist_id],
            )

        print("Album and artist counts updated")

    def serialize_data(self, data):
        serializer = MusicSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer

    def create_music_artist(self, user_id):
        data = self.data
        self.serialize_data(data)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT uuid
                FROM artists_artist
                WHERE user_id = %s
                """,
                [user_id],
            )
            artist = c.fetchone()
            if artist is None:
                return Response(
                    {"message": "Artist not found"}, status=status.HTTP_404_NOT_FOUND
                )
            artist_dict = convert_tuples_to_dicts(artist, ["uuid"])[0]
            artist_id = artist_dict["uuid"]

            c.execute(
                """
                INSERT INTO musics_music
                (title, album_id, genre, artist_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING uuid, title, album_id, genre, artist_id
                """,
                [
                    data.get("title", ""),
                    data.get("album", None),
                    data.get("genre", ""),
                    artist_id,
                ],
            )
            music = c.fetchone()
            album_id = music[2]
            artist_id = music[4]
            self.update_album_and_artist_counts(album_id, artist_id)
            if music is None:
                return Response(
                    {"message": "Music not created"}, status=status.HTTP_400_BAD_REQUEST
                )
            music_dict = convert_tuples_to_dicts(
                music,
                [
                    "uuid",
                    "title",
                    "album_id",
                    "genre",
                    "artist_id",
                ],
            )[0]
            return Response(music_dict, status=status.HTTP_200_OK)

    def create_music_manager(self):
        data = self.data
        self.serialize_data(data)
        artist_id = data.get("artist", None) or None
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO musics_music
                (title, album_id, genre, artist_id, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING uuid, title, album_id, genre, artist_id
                """,
                [
                    data.get("title", ""),
                    data.get("album", None),
                    data.get("genre", ""),
                    artist_id,
                ],
            )
            music = c.fetchone()
            album_id = music[2]
            artist_id = music[4]
            self.update_album_and_artist_counts(album_id, artist_id)
            if music is None:
                return Response(
                    {"message": "Music not created"}, status=status.HTTP_400_BAD_REQUEST
                )
            music_dict = convert_tuples_to_dicts(
                music,
                [
                    "uuid",
                    "title",
                    "album_id",
                    "genre",
                    "artist_id",
                ],
            )[0]
            return Response(music_dict, status=status.HTTP_200_OK)

    def create_music(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        role = payload.get("role", "")
        user_id = payload.get("user_id", "")

        if role != "ARTIST" and role != "ARTIST_MANAGER":
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if role == "ARTIST":
            return self.create_music_artist(user_id)

        if role == "ARTIST_MANAGER":
            return self.create_music_manager()

    def update_music(self, uuid):
        data = self.data
        self.serialize_data(data)
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE musics_music
                SET title = %s, album_id = %s, genre = %s, artist_id = %s, updated_at = NOW()
                WHERE uuid = %s
                RETURNING uuid, title, album_id, genre, artist_id
                """,
                [
                    data.get("title", ""),
                    data.get("album", None),
                    data.get("genre", ""),
                    data.get("artist", None),
                    uuid,
                ],
            )
            music = c.fetchone()
            album_id = music[2]
            artist_id = music[4]
            self.update_album_and_artist_counts(album_id, artist_id)
        if music is None:
            return Response(
                {"message": "Music not updated"}, status=status.HTTP_400_BAD_REQUEST
            )
        music_dict = convert_tuples_to_dicts(
            music,
            [
                "uuid",
                "title",
                "album_id",
                "genre",
                "artist_id",
            ],
        )[0]
        return Response(music_dict, status=status.HTTP_200_OK)

    def delete_music(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                DELETE FROM musics_music
                WHERE uuid = %s
                RETURNING True, album_id, artist_id
                """,
                [uuid],
            )

            music = c.fetchone()
            album_id = music[1]
            artist_id = music[2]
            self.update_album_and_artist_counts(album_id, artist_id)
            return c.fetchone()[0]
