from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Music
from apps.musics.selectors import MusicSelector
from apps.musics.services import MusicService
from apps.users.authentication import JWTAuthentication


class GenreView(APIView):
    def get(self, request):
        genres = [genre[0] for genre in Music.Genre.choices]
        return Response(genres, status=status.HTTP_200_OK)


class MusicView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        musicSelector = MusicSelector(request.headers)
        return musicSelector.get_musics()

    def post(self, request):
        musicService = MusicService(request.data, request.headers)
        return musicService.create_music()


class MusicDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        musicSelector = MusicSelector(request.headers)
        return musicSelector.get_music_by_id(uuid)

    def put(self, request, uuid):
        musicService = MusicService(request.data, request.headers)
        return musicService.update_music(uuid)

    def delete(self, request, uuid):
        musicService = MusicService(request.data, request.headers)
        return musicService.delete_music(uuid)
