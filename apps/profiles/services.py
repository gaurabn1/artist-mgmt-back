from django.contrib.auth.hashers import make_password
from django.db import connection, transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.selectors import ManagerSelector
from apps.profiles.serializers import UserProfileSerializer
from apps.users.utils import get_payload


class ManagerService:

    def __init__(self, request):
        self.headers = request.headers
        self.data = request.data
        self.request = request

    def serialize_data(self, data):
        serializer = UserProfileSerializer(data=data)
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
                [email, hashed_password, "ARTIST_MANAGER"],
            )
            user = c.fetchone()
            if user is None:
                raise APIException("Failed to create user", status.HTTP_400_BAD_REQUEST)
            user_dict = convert_tuples_to_dicts(user, ["uuid"])[0]
        return user_dict["uuid"]

    def create_manager(self):
        data = self.data
        if not data:
            raise APIException("No data provided", status.HTTP_400_BAD_REQUEST)
        self.serialize_data(data)
        payload = get_payload(self.headers)
        if payload is None:
            raise APIException("Failed to create manager", status.HTTP_401_UNAUTHORIZED)
        if payload["role"] != "SUPER_ADMIN":
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        with transaction.atomic():
            with connection.cursor() as c:
                user_id = (
                    self.create_user_account()
                )  # Create user account and get an id
                c.execute(  # creating manager
                    """
                    INSERT INTO profiles_userprofile
                    (first_name, last_name, dob, gender, address, phone, created_at, updated_at, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                    RETURNING uuid, first_name, last_name, dob, gender, address, phone, user_id
                    """,
                    [
                        data.get("first_name", ""),
                        data.get("last_name", ""),
                        data.get("dob", ""),
                        data.get("gender", ""),
                        data.get("address", ""),
                        data.get("phone", ""),
                        user_id,
                    ],
                )
                manager = c.fetchone()
                columns = [col[0] for col in c.description]
                if manager is None:
                    raise APIException(
                        "Failed to create manager", status.HTTP_400_BAD_REQUEST
                    )
        manager_dict = convert_tuples_to_dicts(manager, columns)[0]
        return Response(manager_dict, status=status.HTTP_201_CREATED)

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

    def update_manager(self, uuid):
        data = self.data
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        self.serialize_data(data)
        managerSelector = ManagerSelector(self.request)
        manager = managerSelector.get_manager_by_id(uuid).data

        if manager is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            # password = data.get("password", None) or None
            # if password is not None:
            #     self.update_user_account()
            with connection.cursor() as c:
                c.execute(
                    """
                    UPDATE profiles_userprofile
                    SET first_name = %s, last_name = %s, dob = %s, gender = %s, address = %s, phone = %s, updated_at = NOW()
                    WHERE uuid = %s
                    RETURNING uuid, first_name, last_name, dob, gender, address, phone, user_id
                    """,
                    [
                        data.get("first_name", manager.get("first_name", "")),
                        data.get("last_name", manager.get("last_name", "")),
                        data.get("dob", manager.get("dob", None)),
                        data.get("gender", manager.get("gender", None)),
                        data.get("address", manager.get("address", "")),
                        data.get("phone", manager.get("phone", "")),
                        uuid,
                    ],
                )
                manager = c.fetchone()
                if manager is None:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                columns = [col[0] for col in c.description]
        manager_dict = convert_tuples_to_dicts(manager, columns)
        return Response(manager_dict, status=status.HTTP_200_OK)

    def delete_manager(self, uuid):
        managerSelector = ManagerSelector(self.request)
        manager = managerSelector.get_manager_by_id(uuid)
        if manager is None:
            return APIException("Manager not found", status.HTTP_404_NOT_FOUND)
        with connection.cursor() as c:
            c.execute(
                "DELETE FROM profiles_userprofile WHERE uuid = %s;",
                [uuid],
            )
            c.execute(
                "DELETE FROM core_user WHERE email = %s;",
                [manager.get("email", "")],
            )
        return manager

    def update_manager_(self, uuid):
        data = self.data
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        managerSelector = ManagerSelector(self.request)
        self.serialize_data(data)
        manager = managerSelector.get_manager_by_id(uuid).data
        if manager is None:
            return APIException("Manager not found", status.HTTP_404_NOT_FOUND)
        if data.get("is_active") is not None or data.get("email") is not None:
            new_email = data.pop("email", manager.get("email", ""))
            is_active = data.pop("is_active", manager.get("is_active", False))
            with connection.cursor() as c:
                c.execute(
                    """
                UPDATE core_user
                SET is_active = %s, email = %s, updated_at = NOW()
                WHERE email = %s
                """,
                    [is_active, new_email, manager.get("email", None)],
                )

            with connection.cursor() as c:
                c.execute(
                    """
                UPDATE profiles_userprofile
                SET first_name = %s, last_name = %s, phone = %s, gender = %s, address = %s, dob = %s, updated_at = NOW()
                WHERE uuid = %s
                RETURNING uuid, first_name, last_name, phone, gender, address, dob
                """,
                    [
                        data.get("first_name", manager.get("first_name", "")),
                        data.get("last_name", manager.get("last_name", "")),
                        data.get("phone", manager.get("phone", "")),
                        data.get("gender", manager.get("gender", "")),
                        data.get("address", manager.get("address", "")),
                        data.get("dob", manager.get("dob", "")),
                        uuid,
                    ],
                )
                manager = c.fetchone()
                columns = [col[0] for col in c.description]
            manager_dict = convert_tuples_to_dicts(manager, columns)[0]
            serializer = UserProfileSerializer(manager_dict)
            return Response(serializer.data, status=status.HTTP_200_OK)
