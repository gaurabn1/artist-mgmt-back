from django.urls import path

from .views import GenreView, MusicDetailView, MusicView

urlpatterns = [
    path("", MusicView.as_view(), name="musics"),
    path("<str:uuid>/", MusicDetailView.as_view(), name="music"),
    path("genres/all/", GenreView.as_view(), name="genres"),
]
