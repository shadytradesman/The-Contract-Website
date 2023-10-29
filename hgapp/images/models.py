from django.conf import settings
from django.db import models
import uuid
import os

from games.models import Scenario

def image_upload_name(instance, filename):
    ext = filename.split('.')[-1]
    filename = "{}.{}".format(uuid.uuid4(), ext)
    return os.path.join('user_images/', filename)


class UserImage(models.Model):
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
        self.file_size = self.image.size
        if self.file_size > 5_000_000:
            raise ValueError("Image too large. Size: " + self.file_size)
        super(UserImage, self).save(*args, **kwargs)
