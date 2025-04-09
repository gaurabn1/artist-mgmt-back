from django.urls import path

from .views import (
    ArtistsByManagersView,
    ManagerArtistView,
    UserProfileDetailView,
    UserProfileView,
)

urlpatterns = [
    path("", UserProfileView.as_view(), name="profiles"),
    path("artists/", ArtistsByManagersView.as_view()),
    path("<str:uuid>/artists/", ManagerArtistView.as_view(), name="manager-artists"),
    path("<str:uuid>/", UserProfileDetailView.as_view(), name="profile"),
]
