from django.contrib import admin

from apps.core.models import Artist


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ["uuid", "name", "no_of_album_released"]
    search_fields = ["name"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
