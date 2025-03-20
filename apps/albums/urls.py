from django.urls import path

from apps.albums.views import AlbumDetailView, AlbumView

urlpatterns = [
    path("", AlbumView.as_view()),
    path("<str:uuid>/", AlbumDetailView.as_view()),
]
