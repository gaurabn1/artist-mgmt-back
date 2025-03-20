from django.db import connection

from apps.profiles.selectors import ManagerSelector
from apps.profiles.serializers import UserProfileSerializer


class ManagerService:
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
        serializer = UserProfileSerializer(manager, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data
