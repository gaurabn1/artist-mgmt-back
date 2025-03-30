from django.db import connection, transaction
from rest_framework import status
from rest_framework.response import Response

from apps.artists.selectors import ArtistSelector
from apps.artists.serializers import ArtistSerializer
from apps.core.utils import convert_tuples_to_dicts


class ArtistService:

    def __init__(self, data=None, headers=None):
        self.data = data
        self.headers = headers

    def serialize_data(self, data):
        serializer = ArtistSerializer(data=data)

        serializer.is_valid(raise_exception=True)
        return serializer

    def create_user_account(self):
        data = self.data
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        email = data.get("email", None)
        password = data.get("password", None)
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO core_user
                (email, password, role, is_active, created_at, updated_at, is_staff, is_superuser)
                VALUES (%s, %s, %s, True, NOW(), NOW(), FALSE, FALSE)
                RETURNING uuid
                """,
                [email, password, "ARTIST"],
            )
            user = c.fetchone()
            if user is None:
                return Response(
                    {"detail": "Failed to create user"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_dict = convert_tuples_to_dicts(user, ["uuid"])[0]
        return user_dict["uuid"]

    def create_artist(self):
        data = self.data
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self.serialize_data(data)
        with transaction.atomic():
            with connection.cursor() as c:
                user_id = self.create_user_account()
                if not isinstance(user_id, str):
                    return user_id
                c.execute(
                    """
                    INSERT INTO artists_artist
                    (name, first_released_year, no_of_album_released, dob, gender, address, manager_id, created_at, updated_at, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                    RETURNING uuid, name, first_released_year, no_of_album_released, dob, gender, address, manager_id, user_id
                    """,
                    [
                        data.get("name", ""),
                        data.get("first_released_year", 0),
                        data.get("no_of_album_released", 0),
                        data.get("dob", ""),
                        data.get("gender", ""),
                        data.get("address", ""),
                        data.get("manager", None),
                        user_id,
                    ],
                )
                artist = c.fetchone()
        if artist is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        artist = convert_tuples_to_dicts(
            artist,
            [
                "uuid",
                "name",
                "first_released_year",
                "no_of_album_released",
                "dob",
                "gender",
                "address",
                "manager_id",
                "user_id",
            ],
        )[0]
        serializer = ArtistSerializer(artist)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update_artist(self, uuid):
        data = self.data
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self.serialize_data(data)
        artistSelector = ArtistSelector(self.headers)
        artist = artistSelector.get_artist_by_id(uuid)
        if artist is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if data.get("is_active") is not None or data.get("email") is not None:
            new_email = data.pop("email", artist.get("email", ""))
            is_active = data.pop("is_active", artist.get("is_active"))
            with connection.cursor() as c:
                c.execute(
                    """
                UPDATE core_user
                SET is_active = %s, email = %s, updated_at = NOW()
                WHERE email = %s
                """,
                    [is_active, new_email, artist.get("email", None)],
                )

        with connection.cursor() as c:
            c.execute(
                """
                UPDATE artists_artist
                SET name = %s, first_released_year = %s, no_of_album_released = %s, dob = %s, gender = %s, address = %s, manager_id = %s, updated_at = NOW()
                WHERE uuid = %s
                RETURNING uuid, name, first_released_year, no_of_album_released, dob, gender, address, manager_id
                """,
                [
                    data.get("name", artist.get("name", "")),
                    data.get(
                        "first_released_year", artist.get("first_released_year", None)
                    ),
                    data.get(
                        "no_of_album_released", artist.get("no_of_album_released", None)
                    ),
                    data.get("dob", artist.get("dob", None)),
                    data.get("gender", artist.get("gender", None)),
                    data.get("address", artist.get("address", "")),
                    data.get("manager", artist.get("manager", None)),
                    uuid,
                ],
            )
            artist = c.fetchone()
            if artist is None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        artist_dict = convert_tuples_to_dicts(
            artist,
            [
                "uuid",
                "name",
                "first_released_year",
                "no_of_album_released",
                "dob",
                "gender",
                "address",
                "manager",
            ],
        )[0]

        serializer = ArtistSerializer(artist_dict)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete_artist(self, uuid):
        artistSelector = ArtistSelector(self.headers)
        artist = artistSelector.get_artist_by_id(uuid)
        if artist is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        with connection.cursor() as c:
            c.execute("DELETE FROM artists_artist WHERE uuid = %s;", [uuid])
            c.execute(
                "DELETE FROM core_user WHERE email = %s;", [artist.get("email", "")]
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
