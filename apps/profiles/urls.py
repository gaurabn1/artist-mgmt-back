from django.urls import path

from .views import ManagerArtistView, UserProfileDetailView, UserProfileView

urlpatterns = [
    path("", UserProfileView.as_view(), name="profiles"),
    path("<str:uuid>/artists/", ManagerArtistView.as_view(), name="manager-artists"),
    path("<str:uuid>/", UserProfileDetailView.as_view(), name="profile"),
]
