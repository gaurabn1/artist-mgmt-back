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


class ArtistCountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        artistSelector = ArtistSelector(request.headers)
        return artistSelector.get_artists_count()


class ArtistView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        artistSelector = ArtistSelector(request.headers)
        return artistSelector.get_artists()

    def post(self, request):
        artistService = ArtistService(request.data, request.headers)
        return artistService.create_artist()


class ArtistDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        artistSelector = ArtistSelector(request.headers)
        return artistSelector.get_artist_by_id(uuid)

    def put(self, request, uuid):
        artistService = ArtistService(request.data, request.headers)
        return artistService.update_artist(uuid)

    def delete(self, request, uuid):
        artistService = ArtistService(request.headers)
        return artistService.delete_artist(uuid)
