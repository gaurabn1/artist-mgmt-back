from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.services import UserService


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
        if result is not None:
            return Response(result, status=status.HTTP_200_OK)
        return Response(
            {"error": "Invalid credentials or user is not active"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
