from django.db import connection
from django.db.models import Count
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.core.models import Artist, Music, UserProfile
from apps.core.utils import convert_tuples_to_dicts
from apps.musics.serializers import MusicSerializer
from apps.users.utils import get_payload


class MusicSelector:
    def __init__(self, request):
        self.headers = request.headers
        self.request = request
        self.page_size = request.query_params.get("page_size", 10)

    def get_music_artist(self, user_id):
        with connection.cursor() as c:
            c.execute(
                """
                    SELECT m.*
                    FROM musics_music m
                    LEFT JOIN artists_artist ar ON m.artist_id = ar.uuid
                    WHERE ar.user_id = %s
                    """,
                [user_id],
            )
            musics = c.fetchall()
            columns = [col[0] for col in c.description]
            if musics is None:
                raise APIException("Musics not found", status.HTTP_404_NOT_FOUND)
        musics_dict = convert_tuples_to_dicts(musics, columns)
        musics_instance = [Music(**music) for music in musics_dict]

        # paginate
        paginator = PageNumberPagination()
        paginator.page_size = self.page_size
        paginated_artists = paginator.paginate_queryset(
            musics_instance, request=self.request
        )

        serializer = MusicSerializer(paginated_artists, many=True)
        return Response(
            paginator.get_paginated_response(serializer.data).data,
            status=status.HTTP_200_OK,
        )

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
                SELECT m.*
                FROM musics_music m
                LEFT JOIN albums_album a ON m.album_id = a.uuid
                LEFT JOIN artists_artist ar ON m.artist_id = ar.uuid
                WHERE ar.manager_id = %s
                """,
                [manager_id],
            )
            musics = c.fetchall()
            columns = [col[0] for col in c.description]
        if musics is None:
            raise APIException("Musics not found", status.HTTP_404_NOT_FOUND)
        musics_dict = convert_tuples_to_dicts(musics, columns)
        musics_instance = [Music(**music) for music in musics_dict]
        # paginate
        paginator = PageNumberPagination()
        paginator.page_size = self.page_size
        paginated_artists = paginator.paginate_queryset(
            musics_instance, request=self.request
        )

        serializer = MusicSerializer(paginated_artists, many=True)
        return Response(
            paginator.get_paginated_response(serializer.data).data,
            status=status.HTTP_200_OK,
        )

    def get_music_admin(self):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT * FROM musics_music
                """
            )
            musics = c.fetchall()
            columns = [col[0] for col in c.description]
        if musics is None:
            raise APIException("Musics not found", status.HTTP_404_NOT_FOUND)
        musics_dict = convert_tuples_to_dicts(musics, columns)
        musics_instance = [Music(**music) for music in musics_dict]
        # paginate
        paginator = PageNumberPagination()
        paginator.page_size = self.page_size
        paginated_artists = paginator.paginate_queryset(
            musics_instance, request=self.request
        )

        serializer = MusicSerializer(paginated_artists, many=True)
        return Response(
            paginator.get_paginated_response(serializer.data).data,
            status=status.HTTP_200_OK,
        )

    def get_musics(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_role = payload.get("role", "")
        user_id = payload.get("user_id", "")

        if (
            user_role != "ARTIST"
            and user_role != "ARTIST_MANAGER"
            and user_role != "SUPER_ADMIN"
        ):
            raise APIException("Unauthorized", status.HTTP_401_UNAUTHORIZED)

        if user_role == "ARTIST":
            return self.get_music_artist(user_id)

        if user_role == "ARTIST_MANAGER":
            return self.get_music_manager(user_id)

        if user_role == "SUPER_ADMIN":
            return self.get_music_admin()

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
            columns = [col[0] for col in c.description]
        if music is None:
            APIException("Music not found", status.HTTP_404_NOT_FOUND)
        music_dict = convert_tuples_to_dicts(music, columns)
        music_instance = [Music(**music) for music in music_dict]
        serializer = MusicSerializer(music_instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_genre_music_count(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_role = payload.get("role", "")
        user_id = payload.get("user_id", "")

        if (
            user_role != "ARTIST"
            and user_role != "ARTIST_MANAGER"
            and user_role != "SUPER_ADMIN"
        ):
            raise APIException("Unauthorized", status.HTTP_401_UNAUTHORIZED)

        musics_count = None
        if user_role == "ARTIST":
            artist_id = Artist.objects.get(user_id=user_id).uuid
            musics = Music.objects.filter(artist_id=artist_id)
            musics_count = (
                musics.values("genre").annotate(count=Count("genre")).order_by("genre")
            )
        if user_role == "ARTIST_MANAGER":
            manager = UserProfile.objects.get(user_id=user_id)
            artists_managed_by_manager = Artist.objects.filter(manager=manager)
            musics = Music.objects.filter(artist__in=artists_managed_by_manager)
            musics_count = (
                musics.values("genre").annotate(count=Count("genre")).order_by("genre")
            )
        if user_role == "SUPER_ADMIN":
            musics_count = (
                Music.objects.values("genre")
                .annotate(count=Count("genre"))
                .order_by("genre")
            )

        return Response(musics_count, status=status.HTTP_200_OK)
