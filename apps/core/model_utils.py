import uuid

from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseProfileModel(BaseModel):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHERS = "O", "Others"

    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=1, choices=Gender.choices, null=True, blank=True
    )
    address = models.TextField(null=True, blank=True)

    class Meta(BaseModel.Meta):
        abstract = True
