from django.db import models
from django.urls import reverse

from games.models import Game

from characters.models import Character


class Journal(models.Model):
    title = models.CharField(max_length=400)
    content = models.TextField(max_length=74000, null=True, blank=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    owner = models.ForeignKey(Character, on_delete=models.CASCADE)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    edit_date = models.DateTimeField('date last edited', null=True, blank=True)
    is_downtime = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('journals.views.JournalView', args=[str(self.id)])