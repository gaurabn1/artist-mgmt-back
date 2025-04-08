from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.profiles.selectors import ManagerSelector
from apps.profiles.services import ManagerService
from apps.users.authentication import JWTAuthentication


class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        managerSelector = ManagerSelector(request)
        return managerSelector.get_managers()

    def post(self, request):
        managerService = ManagerService(request)
        return managerService.create_manager()


class UserProfileDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        managerSelector = ManagerSelector(request)
        return managerSelector.get_manager_by_id(uuid)

    def put(self, request, uuid):
        managerService = ManagerService(request)
        return managerService.update_manager(uuid)

    def delete(self, request, uuid):
        managerService = ManagerService(request)
        return managerService.delete_manager(uuid)
