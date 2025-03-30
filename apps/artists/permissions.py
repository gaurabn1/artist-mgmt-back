from rest_framework.permissions import BasePermission

from apps.core.models import User


class IsNotArtist(BasePermission):
    """
    Permission that denies access to users with the ARTIST role.
    """

    def has_permission(self, request, view):
        return request.user.role != User.Role.ARTIST
