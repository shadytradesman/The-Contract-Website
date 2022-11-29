from django.conf import settings
from django.db import models
import uuid
import os


def image_upload_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "{}.{}".format(uuid.uuid4(), ext)
    return os.path.join('user_images/', filename)


class UserImage(models.Model):
    image = models.ImageField(upload_to=image_upload_name)
    file_size = models.IntegerField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_date = models.DateTimeField('date created', auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['uploader']),
            models.Index(fields=['uploader', 'file_size']),
        ]

    def save(self, *args, **kwargs):
        self.file_size = self.image.size
        if self.file_size > 3_000_000:
            raise ValueError("Image too large. Size: " + self.file_size)
        super(UserImage, self).save(*args, **kwargs)
