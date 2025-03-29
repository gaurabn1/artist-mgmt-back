from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.albums.selectors import AlbumSelector
from apps.albums.services import AlbumService


class AlbumView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        albumSelector = AlbumSelector(request.headers)
        return albumSelector.get_albums()

    def post(self, request):
        albumService = AlbumService(request.FILES, request.data, request.headers)
        return albumService.create_album()


class AlbumDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        albumService = AlbumSelector(request.headers)
        return albumService.get_album_by_id(uuid)

    def put(self, request, uuid):
        albumService = AlbumService(request.FILES, request.data, request.headers)
        return albumService.update_album(uuid)

    def delete(self, request, uuid):
        albumService = AlbumService(request.FILES, request.data, request.headers)
        return albumService.delete_album(uuid)
