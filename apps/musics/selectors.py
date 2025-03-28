from django.db import connection

from apps.core.utils import convert_tuples_to_dicts
from apps.musics.serializers import MusicSerializer


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

    @staticmethod
    def get_musics():
        with connection.cursor() as c:
            c.execute(
                """
                SELECT m.uuid, m.title, m.album_id, m.genre, ar.uuid as artist_uuid, ar.name as artist_name, a.uuid as album_uuid, a.name as album_name
                FROM musics_music m
                LEFT JOIN albums_album a ON m.album_id = a.uuid
                LEFT JOIN artists_artist ar ON m.artist_id = ar.uuid
                """
            )
            musics = c.fetchall()
        if musics is None:
            return None
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
        return serializer.data

    @staticmethod
    def get_music_by_id(uuid):
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
            return None
        music_dict = convert_tuples_to_dicts(music, MusicSelector.FIELD_NAMES)[0]
        serializer = MusicSerializer(music_dict)
        return serializer.data
