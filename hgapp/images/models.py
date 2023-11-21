from django.conf import settings
from django.db import models
import uuid
import os
from django.core.files.storage import default_storage
from overrides.storage import PrivateS3Storage
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from games.models import Scenario


def image_upload_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "{}.{}".format(uuid.uuid4(), ext)
    return os.path.join('user_images/', filename)


def select_private_storage():
    return default_storage if settings.DEBUG else PrivateS3Storage()


class UserImage(models.Model):
    # always public bucket, do not use unless you have to for rendering scenario uploaded images, etc.
    image = models.ImageField(upload_to=image_upload_name)
    file_size = models.IntegerField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['uploader']),
            models.Index(fields=['uploader', 'file_size']),
            models.Index(fields=['scenario']),
        ]

    def __str__(self):
        return "Uploaded by {} for {}".format(self.uploader.username, self.scenario.title if self.scenario else "an unknown Scenario")

    def save(self, *args, **kwargs):
        existing_pk = self.pk
        self.file_size = self.image.size
        if self.file_size > 5_000_000:
            raise ValueError("Image too large. Size: " + self.file_size)
        super(UserImage, self).save(*args, **kwargs)


class PrivateUserImage(models.Model):
    image = models.ImageField(upload_to=image_upload_name, storage=select_private_storage)
    thumbnail = models.ImageField(upload_to=image_upload_name,
                                  storage=select_private_storage,
                                  null=True) # nullable for async thumbnail generation
    file_size = models.IntegerField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.CharField(max_length=2000, blank=True)
    article = GenericForeignKey() # the world event, journal, etc. Must implement render_timeline_display()

    class Meta:
        indexes = [
            models.Index(fields=['uploader']),
            models.Index(fields=['uploader', 'file_size']),
            models.Index(fields=['content_type']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return "Uploaded by {} for {}".format(self.uploader.username, self.scenario.title if self.scenario else "an unknown Scenario")

    def save(self, *args, **kwargs):
        self.file_size = self.image.size
        if self.file_size > 5_000_000:
            raise ValueError("Image too large. Size: " + self.file_size)
        super(PrivateUserImage, self).save(*args, **kwargs)
