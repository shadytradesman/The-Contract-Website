from django.db import models
import random


class FakeAd(models.Model):
    picture = models.ImageField(null=True, blank=True)
    picture_height = models.IntegerField()
    picture_width = models.IntegerField()
    banner = models.ImageField()
    banner_2 = models.ImageField(blank=True)
    banner_3 = models.ImageField(blank=True)
    headline = models.CharField(max_length=3000)
    subject = models.CharField(max_length=3000)
    content = models.TextField(max_length=20000)
    url = models.TextField(max_length=20000, blank=True)

    def save(self, *args, **kwargs):
        if hasattr(self, "picture") and self.picture is not None:
            self.picture_height = self.picture.height
            self.picture_width = self.picture.width
        super(FakeAd, self).save(*args, **kwargs)

    def get_random_banner(self):
        banners = [self.banner, self.banner_2, self.banner_3]
        banners = [x for x in banners if x is not None]
        random.shuffle(banners)
        return banners[0]
