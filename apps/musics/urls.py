from django.urls import path

from .views import GenreView, MusicCSVView, MusicDetailView, MusicPostBulk, MusicView

urlpatterns = [
    path("", MusicView.as_view(), name="musics"),
    path("csv/", MusicCSVView.as_view(), name="music-csv"),
    path("bulk/", MusicPostBulk.as_view(), name="music-bulk"),
    path("<str:uuid>/", MusicDetailView.as_view(), name="music"),
    path("genres/all/", GenreView.as_view(), name="genres"),
]
