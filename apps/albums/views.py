from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.albums.selectors import AlbumSelector
from apps.albums.serializers import AlbumSerializer
from apps.albums.services import AlbumService
from apps.core.models import Album, User


class AlbumView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result = AlbumSelector.get_albums(request.headers)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def post(self, request):
        result = AlbumService.create_album(request.data, request.FILES, request.headers)
        if result is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED)


class AlbumDetailView(APIView):
    # parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        result = AlbumSelector.get_album_by_id(uuid)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, uuid):
        result = AlbumService.update_album(uuid, request.data, request.FILES)
        if result is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_200_OK)

    def delete(self, request, uuid):
        result = AlbumService.delete_album(uuid)
        if result is not True:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
