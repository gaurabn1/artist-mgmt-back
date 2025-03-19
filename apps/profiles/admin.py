from django.contrib import admin

from apps.core.models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    search_fields = ["user__email"]
    readonly_fields = ["uuid", "created_at", "updated_at"]
