from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services import UserService
from apps.users.utils import JWTManager


class UserRegistrationView(APIView):
    """
    View for user registration and user profile creation
    """

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

    def post(self, request):
        result = UserService.login_user(request.data)
        return result


class RefreshTokenView(APIView):
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
