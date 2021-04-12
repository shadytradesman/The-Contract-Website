from django.db import models
from django.db.models import Q
from django.conf import settings

from bs4 import BeautifulSoup

from django.urls import reverse

from games.models import Game_Attendance, Reward

from characters.models import Character, ExperienceReward

from hgapp.utilities import get_object_or_none

NUM_JOURNALS_PER_IMPROVEMENT = 5

class Journal(models.Model):
    title = models.CharField(max_length=400)
    content = models.TextField(max_length=74000, null=True, blank=True)
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT)
    # The game_attendance field is nullable for cases where a journal is written and the attendance is later deleted.
    # In these cases, the journal is "abandoned": still viewable by the writer, but otherwise unavailable.
    game_attendance = models.ForeignKey(Game_Attendance, null=True, blank=True, on_delete=models.CASCADE)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    edit_date = models.DateTimeField('date last edited', null=True, blank=True)
    is_downtime = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    contains_spoilers = models.BooleanField(default=True)
    experience_reward = models.OneToOneField(ExperienceReward,
                                             null=True,
                                             blank=True,
                                             on_delete=models.SET_NULL)

    class Meta:
        constraints = [
            # You cannot have two non-deleted journals for the same game attendance
            models.UniqueConstraint(fields=['game_attendance'], condition=Q(is_downtime=False, is_deleted=False), name='one_journal_per_game'),
        ]

    def set_content(self, content):
        original_valid = self.is_valid
        is_valid = self.__get_is_valid(content)
        self.is_valid = is_valid
        self.content = content
        self.save()
        if self.is_valid and not original_valid:
            self.grant_reward()
        if original_valid and not self.is_valid:
            self.void_reward()

    def get_improvement(self):
        return get_object_or_none(Reward,
                                  rewarded_player=self.game_attendance.get_player(),
                                  relevant_game=self.game_attendance.relevant_game,
                                  is_void=False,
                                  is_journal=True)


    def get_exp_reward(self):
        if hasattr(self, "experience_reward") and self.experience_reward:
            return self.experience_reward
        else:
            return None

    def void_reward(self):
        improvement = self.get_improvement()
        if improvement:
            improvement.mark_void()
        exp_reward = self.get_exp_reward()
        if exp_reward:
            self.experience_reward.mark_void()
            self.experience_reward = None
            self.save()

    def grant_reward(self):
        if not self.is_valid:
            return
        if hasattr(self, "game_attendance") and self.game_attendance and \
                hasattr(self.game_attendance, "attending_character") and self.game_attendance.attending_character:
            character = self.game_attendance.attending_character
        else:
            return
        journals_until_improvement = self.get_num_journals_until_improvement(character)
        if journals_until_improvement <= 0:
            reward = Reward(relevant_game=Journal.game_attendance.relevant_game,
                                   rewarded_character=character,
                                   rewarded_player=character.player,
                                   is_improvement=True,
                                    is_journal=True)
            reward.save()
        else:
            exp_reward = ExperienceReward(
                rewarded_character=character,
                rewarded_player=character.player,
            )
            exp_reward.save()
            self.experience_reward = exp_reward
            self.save()

    def get_num_journals_until_improvement(character):
        num_valid = Journal.objects.filter(game_attendance__attending_character=character.id,
                                           is_valid=True).count()
        num_journal_rewards = Reward.objects.filter(is_journal=True,
                                                    rewarded_character=character,
                                                    is_improvement=True,
                                                    is_void=False).count()
        needed = NUM_JOURNALS_PER_IMPROVEMENT * (num_journal_rewards + 1)
        return needed - num_valid

    def __get_is_valid(self, content):
        word_count = self.__get_wordcount(content)
        # use slightly fewer words than what we tell people in case our counting sucks
        return word_count >= 246

    def __get_wordcount(self, content):
        soup = BeautifulSoup(content, features="html5lib")
        return len(soup.text.split())

    def player_can_view(self, player):
        return not self.contains_spoilers or self.game_attendance.relevant_game.scenario.player_can_view(player)

    ## Experimental field injection for journal read.
    def inject_viewable(self, player):
        self.is_viewale_by_reader = self.player_can_view(player)

    def save(self, *args, **kwargs):
        if not self.pk and self.content:
            raise ValueError("Set Journal content through set_content()")
        super(Journal, self).save(*args, **kwargs)


class JournalCover(models.Model):
    title = models.CharField(max_length=400)
    content = models.TextField(max_length=74000, null=True, blank=True)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['character'], name='one_cover_per_contractor'),
        ]
