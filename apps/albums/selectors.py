from django.db import connection
from rest_framework import status
from rest_framework.response import Response

from apps.albums.serializers import AlbumSerializer
from apps.core.utils import convert_tuples_to_dicts
from apps.users.utils import get_payload


class AlbumSelector:
    FIELD_NAMES = [
        "uuid",
        "name",
        "owner_id",
        "no_of_tracks",
        "image",
        "owner",
    ]

    def __init__(self, headers):
        self.headers = headers

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
            artist_dict = convert_tuples_to_dicts(artist, ["uuid"])[0]
            artist_id = artist_dict["uuid"]

            ##### Get albums by artist
            c.execute(
                """
                SELECT  a.uuid, a.name, a.owner_id, a.no_of_tracks, a.image, b.name as owner
                FROM albums_album a
                JOIN artists_artist b ON a.owner_id = b.uuid
                WHERE a.owner_id = %s
                """,
                [artist_id],
            )
            albums = c.fetchall()
            if albums is None:
                return Response(
                    {"detail": "Album not found"}, status=status.HTTP_404_NOT_FOUND
                )
            albums_dict = convert_tuples_to_dicts(albums, self.FIELD_NAMES)
            serializer = AlbumSerializer(albums_dict, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

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
                return Response(
                    {"detail": "Manager not found"}, status=status.HTTP_404_NOT_FOUND
                )
            manager_dict = convert_tuples_to_dicts(manager, ["uuid"])[0]
            manager_id = manager_dict["uuid"]

            # Get albums of manager's artists
            c.execute(
                """
                SELECT  a.uuid, a.name, a.owner_id, a.no_of_tracks, a.image, b.name as owner
                FROM albums_album a
                JOIN artists_artist b ON a.owner_id = b.uuid
                WHERE b.manager_id = %s
                """,
                [manager_id],
            )
            albums = c.fetchall()
            if albums is None:
                return Response(
                    {"detail": "Album not found"}, status=status.HTTP_404_NOT_FOUND
                )
            albums_dict = convert_tuples_to_dicts(albums, self.FIELD_NAMES)
            serializer = AlbumSerializer(albums_dict, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    def get_albums(self):
        user_payload = get_payload(self.headers)
        if user_payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_role = user_payload.get("role", "")  # Get user role
        user_id = user_payload.get("user_id", "")  # Get user id

        # Unauthorized other than artist and artist manager
        if user_role != "ARTIST" and user_role != "ARTIST_MANAGER":
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if user_role == "ARTIST":
            return self.get_album_artist(user_id)

        if user_role == "ARTIST_MANAGER":
            return self.get_album_manager(user_id)

    def get_album_by_id(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT  uuid, name, owner_id, no_of_tracks, image
                FROM albums_album
                WHERE uuid = %s
                """,
                [uuid],
            )
            album = c.fetchone()
        if album is None:
            return Response(
                {"detail": "Album not found"}, status=status.HTTP_404_NOT_FOUND
            )
        album = convert_tuples_to_dicts(album, AlbumSelector.FIELD_NAMES)[0]
        serializer = AlbumSerializer(album)
        return Response(serializer.data, status=status.HTTP_200_OK)
