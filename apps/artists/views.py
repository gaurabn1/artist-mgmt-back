from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.artists.selectors import ArtistSelector
from apps.artists.services import ArtistService
from apps.users.authentication import JWTAuthentication


class ArtistCurrectView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        artistSelector = ArtistSelector(request.headers)
        return artistSelector.get_currect_artist()


class ArtistView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        artistSelector = ArtistSelector(request.headers)
        return artistSelector.get_artists()


class ArtistDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        result = ArtistSelector.get_artist_by_id(uuid)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def put(self, request, uuid):
        result = ArtistService.update_artist(uuid, request.data)
        if result is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(result, status=status.HTTP_200_OK)

    def delete(self, request, uuid):
        is_deleted = ArtistService.delete_artist(uuid)
        if is_deleted is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
