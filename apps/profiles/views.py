from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles.selectors import ManagerSelector
from apps.profiles.services import ManagerService
from apps.users.authentication import JWTAuthentication

from .serializers import UserProfileSerializer


class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        managerSelector = ManagerSelector(request.headers)
        return managerSelector.get_managers()


class UserProfileDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        manager = ManagerSelector.get_manager_by_id(uuid)
        if manager is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileSerializer(manager)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, uuid):
        result = ManagerService.update_manager(uuid, request.data)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def delete(self, request, uuid):
        result = ManagerService.delete_manager(uuid)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
