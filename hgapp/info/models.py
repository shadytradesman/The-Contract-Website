from django.db import models

class FrontPageInfo(models.Model):
    shown_fiction = models.TextField(max_length=30000)
    hidden_fiction = models.TextField(max_length=30000)
