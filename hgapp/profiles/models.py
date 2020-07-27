from django.db import models
from django.conf import settings


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    about = models.TextField(max_length=10000)
    confirmed_agreements = models.BooleanField(default=False)
    date_confirmed_agreements = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username
