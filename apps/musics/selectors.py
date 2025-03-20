from django.db import connection

from apps.core.utils import convert_tuples_to_dicts
from apps.musics.serializers import MusicSerializer


class MusicSelector:
    FIELD_NAMES = ["uuid", "title", "album", "genre", "artist"]

    @staticmethod
    def get_musics():
        with connection.cursor() as c:
            c.execute(
                """
                SELECT uuid, title, album_id, genre, artist_id
                FROM musics_music; 
                """
            )
            musics = c.fetchall()
        if musics is None:
            return None
        musics = convert_tuples_to_dicts(musics, MusicSelector.FIELD_NAMES)
        serializer = MusicSerializer(musics, many=True)
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
