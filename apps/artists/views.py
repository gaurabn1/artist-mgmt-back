from os import stat

from django.db import connection
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import APIView, Response

from apps.artists.selectors import ArtistSelector
from apps.artists.serializers import ArtistSerializer
from apps.artists.services import ArtistService
from apps.core.models import Artist
from apps.core.utils import convert_tuples_to_dicts


class ArtistDataView(APIView):
    def get(self, request):
        artistSelector = ArtistSelector(request)
        return artistSelector.get_artists_data()


class ArtistCountView(APIView):
    def get(self, request):
        artistSelector = ArtistSelector(request)
        return artistSelector.get_artists_count()


class ArtistView(APIView):
    permission_classes = []

    def get(self, request):
        artistSelector = ArtistSelector(request)
        return artistSelector.get_artists()

    def post(self, request):
        artistService = ArtistService(request)
        return artistService.create_artist()


class ArtistDetailView(APIView):
    def get(self, request, uuid):
        artistSelector = ArtistSelector(request)
        return artistSelector.get_artist_by_id(uuid)

    def put(self, request, uuid):
        artistService = ArtistService(request)
        return artistService.update_artist(uuid)

    def delete(self, request, uuid):
        artistService = ArtistService(request)
        return artistService.delete_artist(uuid)
