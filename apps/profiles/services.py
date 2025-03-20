from django.db import connection

from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.selectors import ManagerSelector
from apps.profiles.serializers import UserProfileSerializer


class ManagerService:

    @staticmethod
    def serialize_data(data):
        serializer = UserProfileSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer

    @staticmethod
    def delete_manager(uuid):
        manager = ManagerSelector.get_manager_by_id(uuid)
        if manager is None:
            return None
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

    @staticmethod
    def update_manager(uuid, data):
        ManagerService.serialize_data(data)
        manager = ManagerSelector.get_manager_by_id(uuid)
        if manager is None:
            return None
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
            manager_dict = convert_tuples_to_dicts(
                manager, ManagerSelector.FIELD_NAMES
            )[0]
            serializer = UserProfileSerializer(manager_dict)
            return serializer.data
