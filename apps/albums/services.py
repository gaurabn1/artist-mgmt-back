import os
import uuid

from django.conf import settings
from django.db import connection

from apps.albums.selectors import AlbumSelector
from apps.albums.serializers import AlbumSerializer
from apps.core.utils import convert_tuples_to_dicts


class AlbumService:

    @staticmethod
    def save_image(image, data):
        # Serialize and validate
        serializer = AlbumSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        image_name = f"{uuid.uuid4()}_{image.name}"
        image_path = os.path.join(settings.MEDIA_ROOT, "albums", image_name)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as f:
            for chunk in image.chunks():
                f.write(chunk)
        return f"albums/{image_name}"

    @staticmethod
    def create_album(data, files):
        data = data.copy()
        image = files.get("image", None)
        data["image"] = image

        # extract files path and save files
        image_path = AlbumService.save_image(image, data) if image else None
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO albums_album
                (name, owner_id, image, no_of_tracks, created_at, updated_at)
                VALUES (%s, %s, %s, %s, NOW(), NOW())
                RETURNING uuid, name, owner_id, no_of_tracks, image
                """,
                [
                    data.get("name", ""),
                    data.get("owner", None),
                    image_path,
                    data.get("no_of_tracks", 0),
                ],
            )
            album = c.fetchone()
            if album is None:
                return None

            album_dict = convert_tuples_to_dicts(
                album,
                [
                    "uuid",
                    "name",
                    "owner_id",
                    "no_of_tracks",
                    "image",
                ],
            )[0]
        return album_dict

    @staticmethod
    def update_album(uuid, data, files):
        data = data.copy()
        image = files.get("image", None)
        data["image"] = image

        # extract files path and save files
        image_path = AlbumService.save_image(image, data) if image else None

        album = AlbumSelector.get_album_by_id(uuid)
        if album is None:
            return None
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE albums_album
                SET name = %s, owner_id = %s, image = %s, no_of_tracks = %s, updated_at = NOW()
                WHERE uuid = %s
                RETURNING uuid, name, owner_id, no_of_tracks, image
                """,
                [
                    data.get("name", album.get("name", "")),
                    data.get("owner", album.get("owner", None)),
                    image_path,
                    data.get("no_of_tracks", album.get("no_of_tracks", 0)),
                    album.get("uuid", ""),
                ],
            )

            album = c.fetchone()
            if album is None:
                return None

            album_dict = convert_tuples_to_dicts(
                album,
                [
                    "uuid",
                    "name",
                    "owner_id",
                    "no_of_tracks",
                    "image",
                ],
            )[0]
        return album_dict

    @staticmethod
    def delete_album(uuid):
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
        return is_deleted
