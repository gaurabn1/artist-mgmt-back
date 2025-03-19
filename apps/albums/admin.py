from django.contrib import admin

from apps.core.models import Album


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("name", "no_of_tracks")
