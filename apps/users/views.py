from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.artists.selectors import ArtistSelector
from apps.profiles.selectors import ManagerSelector
from apps.users.services import UserService
from apps.users.utils import JWTManager, get_payload


class UserRegistrationView(APIView):
    """
    View for user registration and user profile creation
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request):
        try:
            result = UserService.register_user(request.data)
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    View for user login
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        userService = UserService(request, request.data)
        return userService.login_user()


class RefreshTokenView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        refresh_token = request.data.get("refresh_token", None)
        tokens = JWTManager.refresh_jwt_token(refresh_token)
        if tokens:
            access_token, refresh_token = tokens
            return Response(
                {"tokens": {"access": access_token, "refresh": refresh_token}},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class GetUserView(APIView):
    def get(self, request):
        payload = get_payload(request.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if payload["role"] == "ARTIST":
            artistSelector = ArtistSelector(request)
            return artistSelector.get_currect_artist()
        else:
            managerSelector = ManagerSelector(request)
            return managerSelector.get_current_manager()


class RequestForgetPasswordView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        userService = UserService(request, request.data)
        return userService.request_forget_password()


class ResetPasswordView(APIView):
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        userService = UserService(request, request.data)
        return userService.reset_password()
