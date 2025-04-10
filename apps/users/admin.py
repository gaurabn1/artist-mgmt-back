from django.contrib import admin

from apps.core.models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ["email"]
    readonly_fields = [
        "uuid",
        "created_at",
        "updated_at",
        "last_login",
        "is_staff",
        "is_superuser",
    ]
    list_display = ["email", "role", "is_active"]
    inlines = [UserProfileInline]

    def save_model(self, request, obj, form, change):
        if obj.password:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
