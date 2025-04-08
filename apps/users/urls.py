from django.urls import path

from .views import GetUserView, RefreshTokenView, UserLoginView, UserRegistrationView

urlpatterns = [
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="refresh"),
    path("me/", GetUserView.as_view(), name="me"),
]
