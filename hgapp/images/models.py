from django.conf import settings
from django.db import models
import uuid
import os
from django.core.files.storage import default_storage
from overrides.storage import PrivateS3Storage
from .templatetags.image_tags import image_thumb
from django.utils.safestring import mark_safe
from django.template import loader



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
    scenario = models.CharField(null=True, max_length=2000)

    class Meta:
        indexes = [
            models.Index(fields=['uploader']),
            models.Index(fields=['uploader', 'file_size']),
            models.Index(fields=['scenario']),
        ]

    def __str__(self):
        return "Uploaded by {} for scenario {}".format(self.uploader.username, self.scenario if self.scenario else "an unknown Scenario")

    def save(self, *args, **kwargs):
        self.file_size = self.image.size
        if self.file_size > 5_000_000:
            raise ValueError("Image too large. Size: " + str(self.file_size))
        super(UserImage, self).save(*args, **kwargs)


class PrivateUserImage(models.Model):
    image = models.ImageField(upload_to=image_upload_name, storage=select_private_storage)
    image_height = models.IntegerField(default=0)
    image_width = models.IntegerField(default=0)
    thumbnail = models.ImageField(upload_to=image_upload_name,
                                  storage=select_private_storage,
                                  null=True) # nullable for async thumbnail generation
    thumbnail_height = models.IntegerField(default=0)
    thumbnail_width = models.IntegerField(default=0)
    file_size = models.IntegerField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['uploader']),
            models.Index(fields=['uploader', 'file_size']),
        ]

    def __str__(self):
        return "Uploaded by {}".format(self.uploader.username)

    def save(self, *args, **kwargs):
        self.file_size = self.image.size
        self.image_height = self.image.height if self.image.height else 0
        self.image_width = self.image.width if self.image.width else 0
        if self.file_size > 5_000_000:
            raise ValueError("Image too large. Size: " + str(self.file_size))
        super(PrivateUserImage, self).save(*args, **kwargs)

    def is_too_small_for_thumb(self):
        # if image_width failed to populate, just assume it is big
        if self.image_width == 0:
            return False
        return self.image_width <= settings.THUMB_SIZE[0] and self.image_height <= settings.THUMB_SIZE[1]

    def get_responsible_user(self):
        return self.uploader

    def report_remove(self):
        self.is_deleted = True
        self.save()

    def render_for_report(self):
        context = {
            "image": self
        }
        return mark_safe(loader.get_template("images/image_report_display.html").render(context))
