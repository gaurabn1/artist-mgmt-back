from django.urls import path

from .views import ArtistCountView, ArtistCurrectView, ArtistDetailView, ArtistView

urlpatterns = [
    path("", ArtistView.as_view(), name="artists"),
    path("me/", ArtistCurrectView.as_view(), name="artists"),
    path("count/", ArtistCountView.as_view()),
    path("<str:uuid>/", ArtistDetailView.as_view(), name="artist"),
]
