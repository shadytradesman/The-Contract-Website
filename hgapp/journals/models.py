from django.db import models
from django.db.models import Q
from django.conf import settings

from bs4 import BeautifulSoup

from django.urls import reverse

from games.models import Game_Attendance

from characters.models import Character


class Journal(models.Model):
    title = models.CharField(max_length=400)
    content = models.TextField(max_length=74000, null=True, blank=True)
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT)
    # The game_attendance field is nullable for cases where a journal is written and the attendance is later deleted or altered.
    # In these cases, the journal is "abandoned": still viewable by the writer, but otherwise unavailable.
    game_attendance = models.ForeignKey(Game_Attendance, null=True, blank=True, on_delete=models.CASCADE)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    edit_date = models.DateTimeField('date last edited', null=True, blank=True)
    is_downtime = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    contains_spoilers = models.BooleanField(default=True)

    class Meta:
        constraints = [
            # You cannot have two non-deleted journals for the same game attendance
            models.UniqueConstraint(fields=['game_attendance'], condition=Q(is_downtime=False, is_deleted=False), name='one_journal_per_game'),
        ]

    def __get_is_valid(self, content):
        word_count = self.__get_wordcount(content)
        # use slightly fewer words than what we tell people in case our counting sucks
        return word_count >= 246

    def __get_wordcount(self, content):
        soup = BeautifulSoup(content)
        return len(soup.text.split())
        return count

    def save(self, *args, **kwargs):
        is_valid = self.__get_is_valid(self.content)
        self.is_valid = is_valid
        super(Journal, self).save(*args, **kwargs)

