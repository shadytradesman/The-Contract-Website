from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    about = models.TextField(max_length=10000)

    def __str__(self):
        return self.user.username
