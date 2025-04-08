from django.db import connection
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.artists.serializers import ArtistSerializer
from apps.core.models import UserProfile
from apps.core.utils import convert_tuples_to_dicts
from apps.profiles.serializers import UserProfileSerializer
from apps.users.utils import get_payload


class ManagerSelector:
    def __init__(self, request):
        self.headers = request.headers
        self.request = request
        self.page_size = request.query_params.get("page_size", 10)

    def get_managers(self):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT m.*
                FROM profiles_userprofile m
                JOIN core_user u ON u.uuid = m.user_id
                WHERE u.role = 'ARTIST_MANAGER';
                """
            )
            managers = c.fetchall()
            columns = [col[0] for col in c.description]
            if managers is None:
                return Response(status=status.HTTP_404_NOT_FOUND)
        managers_dict = convert_tuples_to_dicts(managers, columns)
        managers_instances = [UserProfile(**manager) for manager in managers_dict]

        # paginate
        paginator = PageNumberPagination()
        paginator.page_size = self.page_size
        paginated_managers = paginator.paginate_queryset(
            managers_instances, request=self.request
        )
        serializer = UserProfileSerializer(paginated_managers, many=True)
        return Response(
            paginator.get_paginated_response(serializer.data).data,
            status=status.HTTP_200_OK,
        )

    def get_manager_by_id(self, uuid):
        with connection.cursor() as c:
            c.execute(
                """
                SELECT m.*
                FROM core_user u
                JOIN profiles_userprofile m ON u.uuid = m.user_id
                WHERE u.role = 'ARTIST_MANAGER' AND m.uuid = %s
                """,
                [uuid],
            )
            manager = c.fetchone()
            columns = [col[0] for col in c.description]
        if manager is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        managers_dict = convert_tuples_to_dicts(manager, columns)
        managers_instances = [UserProfile(**manager) for manager in managers_dict]

        serializer = UserProfileSerializer(managers_instances, many=True)
        return Response(serializer.data[0], status=status.HTTP_200_OK)

    def get_current_manager(self):
        payload = get_payload(self.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        user_id = payload.get("user_id", "")
        with connection.cursor() as c:
            c.execute(
                """
                SELECT uuid
                FROM profiles_userprofile
                WHERE user_id = %s
                
                """,
                [user_id],
            )
            manager_id = c.fetchone()
            if not manager_id:
                return Response(status=status.HTTP_404_NOT_FOUND)
            manager_id = manager_id[0]
        if user_id is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return self.get_manager_by_id(manager_id)

    def get_artists_by_managers(self, uuid):
        manager = UserProfile.objects.get(uuid=uuid)
        serializer = UserProfileSerializer(manager)
        artists = manager.artists_managed.all()
        response = serializer.data
        response["artists"] = ArtistSerializer(artists, many=True).data
        return Response(response, status=status.HTTP_200_OK)
