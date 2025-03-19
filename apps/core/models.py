import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from .managers import CustomUserManager
from .model_utils import BaseModel, BaseProfileModel


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        ARTIST_MANAGER = "ARTIST_MANAGER", "Artist Manager"
        ARTIST = "ARTIST", "Artist"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.email


class UserProfile(BaseProfileModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile_user"
    )

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    class Meta(BaseProfileModel.Meta):
        app_label = "profiles"
        verbose_name = "User Profile"


class Artist(BaseProfileModel):
    name = models.CharField(max_length=100)
    first_released_year = models.IntegerField(null=True, blank=True)
    no_of_album_released = models.IntegerField(null=True, blank=True, default=0)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="artist_user"
    )
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="artists_managed",
        limit_choices_to={"role": User.Role.ARTIST_MANAGER},
    )

    class Meta(BaseProfileModel.Meta):
        ordering = ["name"]
        app_label = "artists"

    def clean(self):
        if self.manager and self.manager.role != User.Role.ARTIST_MANAGER:
            raise ValidationError("Manager must be an artist manager.")

        if self.first_released_year:
            current_year = datetime.datetime.now().year
            if not (1900 <= self.first_released_year <= current_year):
                raise ValidationError(
                    "First released year must be between 1900 and the current year."
                )

    def __str__(self) -> str:
        return self.name


class Album(BaseModel):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="album/", null=True, blank=True)
    no_of_tracks = models.IntegerField(null=True, blank=True, default=0)
    owner = models.ForeignKey(
        Artist, on_delete=models.SET_NULL, null=True, related_name="albums"
    )

    class Meta(BaseModel.Meta):
        ordering = ["name"]
        app_label = "albums"

    def __str__(self) -> str:
        return self.name


class Music(BaseModel):
    class Genre(models.TextChoices):
        ROCK = "ROCK", "Rock"
        POP = (
            "POP",
            "Pop",
        )
        COUNTRY = (
            "COUNTRY",
            "Country",
        )
        CLASSICAL = (
            "CLASSICAL",
            "Classical",
        )
        JAZZ = "JAZZ", "Jazz"

    title = models.CharField(max_length=100)
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True)
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, null=True)
    genre = models.CharField(max_length=20, choices=Genre.choices)

    def __str__(self) -> str:
        return self.title

    class Meta(BaseModel.Meta):
        app_label = "musics"
