from django.db import models


class FakeAd(models.Model):
    picture = models.ImageField(null=True, blank=True)
    banner = models.ImageField()
    headline = models.CharField(max_length=3000)
    subject = models.CharField(max_length=3000)
    content = models.TextField(max_length=20000)
