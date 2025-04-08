from django.contrib.auth.hashers import make_password
from django.db import connection, transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from apps.artists.selectors import ArtistSelector
from apps.artists.serializers import ArtistSerializer
from apps.core.models import Artist
from apps.core.utils import convert_tuples_to_dicts
from apps.users.utils import get_payload


class ArtistService:

    def __init__(self, request=None):
        if request is None:
            raise APIException("No request provided", status.HTTP_400_BAD_REQUEST)
        self.request = request
        self.data = request.data
        self.headers = request.headers

    def serialize_data(self, data):
        serializer = ArtistSerializer(data=data)
        if not serializer.is_valid():
            print(serializer.errors)
        serializer.is_valid(raise_exception=True)
        return serializer

    def create_user_account(self):
        data = self.data
        if data is None:
            raise APIException("No data provided", status.HTTP_400_BAD_REQUEST)
        user = data["user"]
        email = user.get("email", None)
        password = user.get("password", None)
        hashed_password = make_password(password)
        with connection.cursor() as c:
            c.execute(
                """
                INSERT INTO core_user
                (email, password, role, is_active, created_at, updated_at, is_staff, is_superuser)
                VALUES (%s, %s, %s, True, NOW(), NOW(), FALSE, FALSE)
                RETURNING uuid
                """,
                [email, hashed_password, "ARTIST"],
            )
            user = c.fetchone()
            if user is None:
                raise APIException("Failed to create user", status.HTTP_400_BAD_REQUEST)
            user_dict = convert_tuples_to_dicts(user, ["uuid"])[0]
        return user_dict["uuid"]

    def create_artist(self):
        data = self.data
        if not data:
            raise APIException("No data provided", status.HTTP_400_BAD_REQUEST)
        self.serialize_data(data)
        payload = get_payload(self.headers)
        if payload is None:
            raise APIException("Failed to create artist", status.HTTP_401_UNAUTHORIZED)

        manager = data.get("manager", None)
        manager_id = manager.get("uuid", None)
        if payload["role"] == "ARTIST_MANAGER":
            manager_userid = payload.get("user_id", None)

            with connection.cursor() as c:  # getting manager id
                c.execute(
                    """
                    SELECT uuid
                    FROM profiles_userprofile
                    WHERE user_id = %s
                    """,
                    [manager_userid],
                )
                manager_id = c.fetchone()
                if manager_id is None:
                    return Response(
                        {"message": "Manager not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            manager_id = manager_id[0]

        with transaction.atomic():
            with connection.cursor() as c:
                user_id = (
                    self.create_user_account()
                )  # create user account and get an id
                c.execute(  # creating artist
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
                        manager_id,
                        user_id,
                    ],
                )
                artist = c.fetchone()
                columns = [col[0] for col in c.description]
        if artist is None:
            raise APIException("Failed to create artist", status.HTTP_400_BAD_REQUEST)
        artist_dict = convert_tuples_to_dicts(artist, columns)[0]
        return Response(artist_dict, status=status.HTTP_201_CREATED)

    def update_user_account(self):
        data = self.data
        if data is None:
            raise APIException("No data provided", status.HTTP_400_BAD_REQUEST)
        user = data["user"]
        email = user.get("email", None)
        password = user.get("password", None)
        hashed_password = make_password(password)
        with connection.cursor() as c:
            c.execute(
                """
                UPDATE core_user
                SET password = %s, updated_at = NOW()
                WHERE email = %s
                """,
                [hashed_password, email],
            )
        return Response(status=status.HTTP_200_OK)

    def update_artist(self, uuid):
        data = self.data
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self.serialize_data(data)
        artistSelector = ArtistSelector(self.request)
        artist = artistSelector.get_artist_by_id(uuid).data
        if artist is None:
            return APIException("Artist not found", status.HTTP_404_NOT_FOUND)
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        manager = artist.get("manager", None)
        manager_id = None
        if manager is not None:
            manager_id = manager.get("uuid", None)
        if payload["role"] == "SUPER_ADMIN":
            manager = data.get("manager", None)
            manager_id = manager.get("uuid", artist.get("manager", None))
        if payload["role"] == "ARTIST_MANAGER":
            manager_userid = payload.get("user_id", None)
            with connection.cursor() as c:  # getting manager id
                c.execute(
                    """
                    SELECT uuid
                    FROM profiles_userprofile
                    WHERE user_id = %s
                    """,
                    [manager_userid],
                )
                manager_id = c.fetchone()
                if manager_id is None:
                    return Response(
                        {"message": "Manager not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            manager_id = manager_id[0]

        if artist is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            password = data.get("password", None) or None
            if password is not None:
                self.update_user_account()
            with connection.cursor() as c:
                c.execute(
                    """
                    UPDATE artists_artist
                    SET name = %s, first_released_year = %s, dob = %s, gender = %s, address = %s, manager_id = %s, updated_at = NOW()
                    WHERE uuid = %s
                    RETURNING uuid, name, first_released_year, no_of_album_released, dob, gender, address, manager_id
                    """,
                    [
                        data.get("name", artist.get("name", "")),
                        data.get(
                            "first_released_year",
                            artist.get("first_released_year", None),
                        ),
                        data.get("dob", artist.get("dob", None)),
                        data.get("gender", artist.get("gender", None)),
                        data.get("address", artist.get("address", "")),
                        manager_id,
                        uuid,
                    ],
                )
                artist = c.fetchone()
                columns = [col[0] for col in c.description]
                if artist is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
        artist_dict = convert_tuples_to_dicts(artist, columns)
        return Response(artist_dict, status=status.HTTP_200_OK)

    def delete_artist(self, uuid):
        artistSelector = ArtistSelector(self.request)
        artist = artistSelector.get_artist_by_id(uuid)
        if artist is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        email = artist.data["user"]["email"]
        with transaction.atomic():
            with connection.cursor() as c:
                c.execute("DELETE FROM artists_artist WHERE uuid = %s;", [uuid])
                c.execute("DELETE FROM core_user WHERE email = %s;", [email])

            return Response(status=status.HTTP_204_NO_CONTENT)
        return APIException("Failed to delete artist", status.HTTP_400_BAD_REQUEST)
