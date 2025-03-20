from django.db import connection
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Album, Artist, Music
from apps.musics.selectors import MusicSelector
from apps.musics.services import MusicService
from apps.users.authentication import JWTAuthentication

from .serializers import MusicSerializer


class GenreView(APIView):
    def get(self, request):
        genres = [genre[0] for genre in Music.Genre.choices]
        return Response(genres, status=status.HTTP_200_OK)


class MusicView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = MusicSelector.get_musics()
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        result = MusicService.create_music(request.data)
        if result is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


class MusicDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        result = MusicSelector.get_music_by_id(uuid)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, uuid):
        result = MusicService.update_music(uuid, request.data)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def delete(self, request, uuid):
        is_deleted = MusicService.delete_music(uuid)
        if is_deleted is not True:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
