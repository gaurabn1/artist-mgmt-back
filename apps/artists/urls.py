from django.urls import path

from .views import ArtistCountView, ArtistDataView, ArtistDetailView, ArtistView

urlpatterns = [
    path("", ArtistView.as_view(), name="artists"),
    path("count/", ArtistCountView.as_view()),
    path("data/", ArtistDataView.as_view()),
    path("<str:uuid>/", ArtistDetailView.as_view(), name="artist"),
]
