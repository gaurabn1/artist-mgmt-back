import os
import uuid

from django.conf import settings
from django.db import connection

from apps.albums.selectors import AlbumSelector
from apps.albums.serializers import AlbumSerializer
from apps.core.utils import convert_tuples_to_dicts
from apps.users.utils import JWTManager


class AlbumService:

    @staticmethod
    def increment_album_count(uuid):
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

    @staticmethod
    def decrement_album_count(uuid):
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
    def create_album(data, files, headers):
        data = data.copy()
        image = files.get("image", None)
        data["image"] = image
        user_payload = JWTManager.decode_jwt_token(
            headers.get("Authorization", "").split(" ")[1]
        )
        user_id = data.get("owner", None)
        if user_payload is not None and user_payload.get("role", "") == "ARTIST":
            user_id = user_payload.get("user_id", "")

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
            artist_dict = convert_tuples_to_dicts(artist, ["uuid"])[0]

            if artist_dict is None:
                return None
            user_id = artist_dict["uuid"]
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
                    user_id,
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

            AlbumService.increment_album_count(data.get("owner", None))
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
                    data.get("owner", album.get("owner_id", None)),
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
