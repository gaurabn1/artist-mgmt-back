import os
import uuid

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from apps.albums.selectors import AlbumSelector
from apps.albums.serializers import AlbumSerializer
from apps.core.utils import convert_tuples_to_dicts
from apps.users.utils import get_payload


class AlbumService:

    def __init__(self, request):
        self.request = request
        self.files = request.FILES
        self.data = request.data
        self.headers = request.headers

    def save_image(self, image):
        # Serialize and validate
        serializer = AlbumSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)

        image_name = f"{uuid.uuid4()}_{image.name}"
        image_path = os.path.join(settings.MEDIA_ROOT, "albums", image_name)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as f:
            for chunk in image.chunks():
                f.write(chunk)
        return f"albums/{image_name}"

    def insert_to_the_database(self, owner_id, image_path):
        data = self.data
        with connection.cursor() as c:
            # Inserting album data into database
            c.execute(
                """
                INSERT INTO albums_album
                (name, owner_id, image, no_of_tracks, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING uuid, name, owner_id, no_of_tracks, image
                """,
                [
                    data.get("name", ""),
                    owner_id,
                    image_path,
                    data.get("no_of_tracks", 0),
                ],
            )
            album = c.fetchone()
            columns = [col[0] for col in c.description]
            if album is None:
                raise APIException("Error creating an album", status.HTTP_404_NOT_FOUND)
            album_dict = convert_tuples_to_dicts(album, columns)[0]
        return Response(album_dict, status=status.HTTP_201_CREATED)

    def update_to_the_database(self, album_id, image_path):
        data = self.data
        with connection.cursor() as c:
            # Updating album data into database
            c.execute(
                """
                UPDATE albums_album
                SET name = %s, image = %s, no_of_tracks = %s, updated_at = NOW()
                WHERE uuid = %s
                RETURNING uuid, name, owner_id, no_of_tracks, image
                """,
                [
                    data.get("name", ""),
                    image_path,
                    data.get("no_of_tracks", 0),
                    album_id,
                ],
            )
            album = c.fetchone()
            columns = [col[0] for col in c.description]
            if album is None:
                return Response(
                    {"detail": "Album not updated"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            album_dict = convert_tuples_to_dicts(album, columns)[0]
        return Response(album_dict, status=status.HTTP_200_OK)

    def create_update_album_artist(
        self, user_id=None, album_id=None, update_image_path=None
    ):
        data = self.data.copy()  # Making a copy of the data
        image = self.files.get("image", None)
        data["image"] = image
        image_path = self.save_image(image) if image else None
        if update_image_path is not None:
            image_path = update_image_path
        if album_id:
            return self.update_to_the_database(album_id, image_path)

        with connection.cursor() as c:
            # Get artist id from user_id
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
            raise APIException("Error creating an album", status.HTTP_404_NOT_FOUND)
        artist_dict = convert_tuples_to_dicts(artist, ["uuid"])[0]
        artist_id = artist_dict["uuid"]
        return self.insert_to_the_database(artist_id, image_path)

    def create_album_manager(self):
        data = self.data.copy()  # Making a copy of the data
        image = self.files.get("image", None)
        data["image"] = image
        owner_id = data.get("owner", None)

        # path where image is saved
        image_path = self.save_image(image) if image else None
        return self.insert_to_the_database(owner_id, image_path)

    def create_album(self):
        user_payload = get_payload(self.headers)
        if user_payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)  # unauthorized user

        user_role = user_payload.get("role", "")
        user_id = user_payload.get("user_id", "")

        # Unauthorized other than artist and artist manager
        if (
            user_role != "ARTIST"
            and user_role != "ARTIST_MANAGER"
            and user_role != "SUPER_ADMIN"
        ):
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        if user_role == "ARTIST":
            return self.create_update_album_artist(user_id=user_id)

        if user_role == "ARTIST_MANAGER" and user_role == "SUPER_ADMIN":
            return self.create_album_manager()

    def update_album(self, uuid):
        albumSelector = AlbumSelector(self.request)
        album = albumSelector.get_album_by_id(uuid)
        if album is None:
            return Response(
                {"detail": "Album not found"}, status=status.HTTP_404_NOT_FOUND
            )
        image_path = None
        if album.data.get("image", None) is not None:
            image_path = album.data.get("image", None)
            if image_path:
                image_path = image_path.split("media/")[1]
        return self.create_update_album_artist(
            album_id=uuid, update_image_path=image_path
        )

    def delete_album(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                DELETE FROM albums_album 
                WHERE uuid = %s
                RETURNING TRUE
                """,
                [uuid],
            )
            is_deleted = c.fetchone()[0]

        if is_deleted is not True:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def increment_album_count(self, uuid):
        with connection.cursor() as c:

            c.execute(
                """
                UPDATE artists_artist
                SET no_of_album_released = no_of_album_released + 1
                WHERE uuid = %s
                """,
                [uuid],
            )
        return

    def decrement_album_count(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE artists_artist
                SET no_of_album_released = no_of_album_released - 1
                WHERE uuid = %s
                """,
                [uuid],
            )
        return
