from django.urls import path

from .views import ArtistDetailView, ArtistView

urlpatterns = [
    path("", ArtistView.as_view(), name="artists"),
    path("<str:uuid>/", ArtistDetailView.as_view(), name="artist"),
]
