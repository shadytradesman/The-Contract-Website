from django.db import models


class BouncedEmail(models.Model):
    email = models.CharField(max_length=900)
    created_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
