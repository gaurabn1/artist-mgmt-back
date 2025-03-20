from django.urls import path

from .views import UserProfileDetailView, UserProfileView

urlpatterns = [
    path("", UserProfileView.as_view(), name="profiles"),
    path("<str:uuid>/", UserProfileDetailView.as_view(), name="profile"),
]
