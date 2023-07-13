from django.db import models
import random


class FakeAd(models.Model):
    picture = models.ImageField(null=True, blank=True)
    banner = models.ImageField()
    banner_2 = models.ImageField(blank=True)
    banner_3 = models.ImageField(blank=True)
    headline = models.CharField(max_length=3000)
    subject = models.CharField(max_length=3000)
    content = models.TextField(max_length=20000)

    def get_random_banner(self):
        banners = [self.banner, self.banner_2, self.banner_3]
        banners = [x for x in banners if x.name]
        random.shuffle(banners)
        return banners[0]
