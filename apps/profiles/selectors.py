from django.db import connection
from rest_framework import status
from rest_framework.response import Response

from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.serializers import UserProfileSerializer


class ManagerSelector:
    FIELD_NAMES = [
        "uuid",
        "first_name",
        "last_name",
        "phone",
        "email",
        "gender",
        "address",
        "dob",
        "is_active",
        "role",
    ]

    def __init__(self, headers):
        self.headers = headers

    def get_managers(self):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT 
                m.uuid, m.first_name, m.last_name, m.phone, u.email, m.gender, m.address, m.dob, u.is_active
                FROM core_user u
                JOIN profiles_userprofile m ON u.uuid = m.user_id
                WHERE u.role = 'ARTIST_MANAGER';
                """
            )
            managers = c.fetchall()
            if managers is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
        managers_data = convert_tuples_to_dicts(managers, ManagerSelector.FIELD_NAMES)
        serializer = UserProfileSerializer(managers_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def get_manager_by_id(uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT 
                m.uuid, m.first_name, m.last_name, m.phone, u.email, m.gender, m.address, m.dob, u.is_active, u.role
                FROM core_user u
                JOIN profiles_userprofile m ON u.uuid = m.user_id
                WHERE u.role = 'ARTIST_MANAGER' AND m.uuid = %s
                """,
                [uuid],
            )
            manager = c.fetchone()
        if manager is None:
            return None
        manager_data = convert_tuples_to_dicts(manager, ManagerSelector.FIELD_NAMES)[0]
        serializer = UserProfileSerializer(manager_data)
        return serializer.data
