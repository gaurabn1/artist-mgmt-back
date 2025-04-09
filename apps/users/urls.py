from django.urls import path

from .views import (
    GetUserView,
    RefreshTokenView,
    RequestForgetPasswordView,
    ResetPasswordView,
    UserLoginView,
    UserRegistrationView,
)

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="refresh"),
    path("me/", GetUserView.as_view(), name="me"),
    path(
        "forget-password/", RequestForgetPasswordView.as_view(), name="forget-password"
    ),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]
