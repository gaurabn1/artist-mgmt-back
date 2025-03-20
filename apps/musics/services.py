from django.db import connection

from apps.core.utils import convert_tuples_to_dicts
from apps.musics.serializers import MusicSerializer


class MusicService:

    @staticmethod
    def serialize_data(data):
        serializer = MusicSerializer(data=data)
        if not serializer.is_valid():
            print(serializer.errors)
        serializer.is_valid(raise_exception=True)
        return serializer

    @staticmethod
    def create_music(data):
        MusicService.serialize_data(data)
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
                    data.get("artist", None),
                ],
            )
            music = c.fetchone()
        if music is None:
            return None

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
        return music_dict

    @staticmethod
    def update_music(uuid, data):
        MusicService.serialize_data(data)
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
        if music is None:
            return None
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
        return music_dict

    @staticmethod
    def delete_music(uuid):
        with connection.cursor() as c:
            c.execute(
                """
                DELETE FROM musics_music
                WHERE uuid = %s
                RETURNING TRUE
                """,
                [uuid],
            )

            is_deleted = c.fetchone()[0]
            return is_deleted
