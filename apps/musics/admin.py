from django.contrib import admin

from apps.core.models import Music


@admin.register(Music)
class MusicAdmin(admin.ModelAdmin):
    list_display = ["uuid", "title"]
    search_fields = ["title"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
