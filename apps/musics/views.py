import csv

from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Artist, Music
from apps.musics.selectors import MusicSelector
from apps.musics.services import MusicService
from apps.users.authentication import JWTAuthentication
from apps.users.utils import get_payload


class MusicPostBulk(APIView):
    def post(self, request):
        musicService = MusicService(request)
        return musicService.create_musics_bulk()


class GenreView(APIView):
    def get(self, request):
        genres = [genre[0] for genre in Music.Genre.choices]
        return Response(genres, status=status.HTTP_200_OK)


class MusicCSVView(APIView):
    def get(self, request):
        musicView = MusicView()
        payload = get_payload(request.headers)
        if payload is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        musics_response = musicView.get(request)

        if isinstance(musics_response, Response) and musics_response.status_code != 200:
            return musics_response

        musics = musics_response.data.get("results", [])
        if payload["role"] == "ARTIST":
            current_artist_id = payload["user_id"]
            musics = [
                music for music in musics if music.get("artist_id") == current_artist_id
            ]
        elif payload["role"] == "ARTIST_MANAGER":
            current_manager_id = payload["user_id"]
            managed_artists = Artist.objects.filter(manager__uuid=current_manager_id)
            managed_artist_ids = [artist.uuid for artist in managed_artists]
            musics = [
                music
                for music in musics
                if music.get("artist_id") in managed_artist_ids
            ]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="musics.csv"'
        writer = csv.writer(response)
        writer.writerow(["album_id", "artist_id", "title", "album", "genre", "artist"])

        for music in musics:
            artist_name = music.get("artist", {}).get("name", "")
            artist_id = music.get("artist_id", "")
            album_name = music.get("album").get("name", "")
            album_id = music.get("album_id", "")
            writer.writerow(
                [
                    album_id,
                    artist_id,
                    music.get("title", ""),
                    album_name,
                    music.get("genre", ""),
                    artist_name,
                ]
            )
        return response


class MusicView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        musicSelector = MusicSelector(request)
        return musicSelector.get_musics()

    def post(self, request):
        musicService = MusicService(request)
        return musicService.create_music()


class MusicDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        musicSelector = MusicSelector(request)
        return musicSelector.get_music_by_id(uuid)

    def put(self, request, uuid):
        musicService = MusicService(request)
        return musicService.update_music(uuid)

    def delete(self, request, uuid):
        musicService = MusicService(request)
        return musicService.delete_music(uuid)


class GenreMusicView(APIView):

    def get(self, request):
        musicSelector = MusicSelector(request)
        return musicSelector.get_genre_music_count()
