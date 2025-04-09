from django.db import connection
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.albums.serializers import AlbumSerializer
from apps.core.models import Album, Music
from apps.core.utils import convert_tuples_to_dicts
from apps.musics.serializers import MusicSerializer
from apps.users.utils import get_payload


class AlbumSelector:

    def __init__(self, request):
        self.headers = request.headers
        self.request = request
        self.page_size = request.query_params.get("page_size", 10)

    def get_album_artist(self, user_id):
        with connection.cursor() as c:
            ###### Get artist id from user id
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
                    {"detail": "Artist not found"}, status=status.HTTP_404_NOT_FOUND
                )
            artist_id = artist[0]

            ##### Get albums by artist
            c.execute(
                """
                SELECT  a.*
                FROM albums_album a
                JOIN artists_artist b ON a.owner_id = b.uuid
                WHERE a.owner_id = %s
                """,
                [artist_id],
            )
            albums = c.fetchall()
            columns = [col[0] for col in c.description]
            if albums is None:
                raise APIException("Albums not found", status.HTTP_404_NOT_FOUND)
            albums_dict = convert_tuples_to_dicts(albums, columns)
            albums_instance = [Album(**album) for album in albums_dict]

            # paginate
            paginator = PageNumberPagination()
            paginator.page_size = self.page_size
            paginated_albums = paginator.paginate_queryset(
                albums_instance, request=self.request
            )

            serializer = AlbumSerializer(paginated_albums, many=True)
            return Response(
                paginator.get_paginated_response(serializer.data).data,
                status=status.HTTP_200_OK,
            )

    def get_album_manager(self, user_id):
        with connection.cursor() as c:
            # Get manager id from user id
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
                raise APIException("Manager not found", status.HTTP_404_NOT_FOUND)
            manager_id = manager[0]

            # Get albums of manager's artists
            c.execute(
                """
                SELECT  a.*
                FROM albums_album a
                JOIN artists_artist b ON a.owner_id = b.uuid
                WHERE b.manager_id = %s
                """,
                [manager_id],
            )
            albums = c.fetchall()
            columns = [col[0] for col in c.description]
            if albums is None:
                return APIException("Albums not found", status.HTTP_404_NOT_FOUND)
            albums_dict = convert_tuples_to_dicts(albums, columns)
            albums_instance = [Album(**album) for album in albums_dict]

            # paginate
            paginator = PageNumberPagination()
            paginator.page_size = self.page_size
            paginated_artists = paginator.paginate_queryset(
                albums_instance, request=self.request
            )

            serializer = AlbumSerializer(paginated_artists, many=True)
            return Response(
                paginator.get_paginated_response(serializer.data).data,
                status=status.HTTP_200_OK,
            )

    def get_albums(self):
        user_payload = get_payload(self.headers)
        if user_payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_role = user_payload.get("role", "")  # Get user role
        user_id = user_payload.get("user_id", "")  # Get user id

        # Unauthorized other than artist and artist manager
        if (
            user_role != "ARTIST"
            and user_role != "ARTIST_MANAGER"
            and user_role != "SUPER_ADMIN"
        ):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if user_role == "ARTIST":
            return self.get_album_artist(user_id)

        if user_role == "ARTIST_MANAGER":
            return self.get_album_manager(user_id)

        with connection.cursor() as c:
            c.execute(
                """
                SELECT * FROM albums_album
                """
            )
            albums = c.fetchall()
            columns = [col[0] for col in c.description]
            if albums is None:
                raise APIException("Albums not found", status.HTTP_404_NOT_FOUND)
            albums_dict = convert_tuples_to_dicts(albums, columns)
            albums_instance = [Album(**album) for album in albums_dict]

            # paginate
            paginator = PageNumberPagination()
            paginator.page_size = self.page_size
            paginated_albums = paginator.paginate_queryset(
                albums_instance, request=self.request
            )

            serializer = AlbumSerializer(paginated_albums, many=True)
            return Response(
                paginator.get_paginated_response(serializer.data).data,
                status=status.HTTP_200_OK,
            )

    def get_album_by_id(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT  *
                FROM albums_album
                WHERE uuid = %s
                """,
                [uuid],
            )
            album = c.fetchone()
            if album is None:
                raise APIException("Album not found", status.HTTP_404_NOT_FOUND)
            columns = [col[0] for col in c.description]
        album_dict = convert_tuples_to_dicts(album, columns)
        album_instance = [Album(**album) for album in album_dict]
        serializer = AlbumSerializer(album_instance[0])

        # Get musics by album id
        musics = Music.objects.filter(album__uuid=uuid)
        response_data = serializer.data
        response_data["musics"] = MusicSerializer(musics, many=True).data
        return Response(response_data, status=status.HTTP_200_OK)
