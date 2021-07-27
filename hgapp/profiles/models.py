from django.db import models
from django.conf import settings
from django.contrib.auth.models import Permission
from .apps import ProfilesConfig

from django.utils import timezone
from games.models import Game
from games.games_constants import get_completed_game_invite_excludes_query, get_completed_game_excludes_query

PLAYER_PREFIX = (
    ('UNTESTED', 'Untested'),
    ('SHELTERED', 'Sheltered'),
    ('UNLUCKY', 'Unlucky'),
    ('RESOURCEFUL', 'Resourceful'),
    ('DEVIOUS', 'Devious'),
    ('TORTURED', 'Tortured'),
    ('CALCULATING', 'Calculating'),
    ('INGENIOUS', 'Ingenious'),
)

PLAYER_SUFFIX = (
    ('NEWBIE', 'Newbie'),
    ('NOVICE', 'Novice'),
    ('ADEPT', 'Adept'),
    ('PROFESSIONAL', 'Professional'),
    ('VETERAN', 'Veteran'),
)

GM_PREFIX = (
    ('PILLOW', 'Pillow'),
    ('BENEVOLENT', 'Benevolent'),
    ('JUST', 'Just'),
    ('SADISTIC', 'Sadistic'),
    ('CRUEL', 'Cruel'),
)

GM_SUFFIX = (
    ('SPECTATOR', 'Spectator'),
    ('REFEREE', 'Referee'),
    ('BOSS', 'Boss'),
    ('RULER', 'Ruler'),
    ('GOD', 'God'),
)

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    about = models.TextField(max_length=10000)
    confirmed_agreements = models.BooleanField(default=False)
    date_confirmed_agreements = models.DateTimeField(blank=True, null=True)
    player_prefix = models.CharField(choices=PLAYER_PREFIX,
                                     max_length=25,
                                     default=PLAYER_PREFIX[0][0])
    player_suffix = models.CharField(choices=PLAYER_SUFFIX,
                                     max_length=25,
                                     default=PLAYER_SUFFIX[0][0])
    gm_prefix = models.CharField(choices=GM_PREFIX,
                                 max_length=25,
                                 blank=True,
                                 null=True)
    gm_suffix = models.CharField(choices=GM_SUFFIX,
                                 max_length=25,
                                 default=GM_SUFFIX[0][0])
    num_games_gmed = models.IntegerField(blank=True, null=True)
    num_gm_kills = models.IntegerField(blank=True, null=True)
    num_gm_victories = models.IntegerField(blank=True, null=True)
    num_gm_losses = models.IntegerField(blank=True, null=True)
    num_golden_ratios = models.IntegerField(blank=True, null=True)

    view_adult_content = models.BooleanField(default=False)
    date_set_adult_content = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username

    # This should be the only way you set the user's adult content prefs
    def update_view_adult_content(self, view_adult_content):
        if view_adult_content != self.view_adult_content:
            self.view_adult_content = view_adult_content
            self.date_set_adult_content = timezone.now()
            self.save()

    def update_gm_stats_if_necessary(self):
        if not hasattr(self, "num_games_gmed") or not self.num_games_gmed:
            self.update_gm_stats()

    def update_gm_stats(self):
        gm_games = self.get_games_where_player_gmed()
        num_gm_games = gm_games.count()
        num_gm_kills = 0
        num_golden_ratio_games = 0
        num_gm_victories = 0
        num_gm_losses = 0
        for game in gm_games:
            num_gm_kills = num_gm_kills + game.number_deaths()
            num_gm_victories = num_gm_victories + game.number_victories()
            num_gm_losses = num_gm_losses + game.number_losses()
            if game.achieves_golden_ratio():
                num_golden_ratio_games = num_golden_ratio_games + 1
        self.num_games_gmed = num_gm_games
        self.num_gm_losses = num_gm_losses
        self.num_gm_kills = num_gm_kills
        self.num_gm_victories = num_gm_victories
        self.num_golden_ratios = num_golden_ratio_games
        self.save()

    def can_view_adult(self):
        return self.view_adult_content

    def recompute_titles(self):
        self.update_gm_stats()
        self.recompute_player_title()
        self.recompute_gm_title()

    def recompute_player_title(self):
        completed_game_invites = self.completed_game_invites()
        number_completed_games = completed_game_invites.count()
        self.player_suffix = self._player_suffix_from_num_games(number_completed_games)[0]

        invites_with_death = self.get_invites_with_death(completed_game_invites)
        invites_where_player_died = self.get_invites_where_player_died(invites_with_death)
        self.player_prefix = self._player_prefix_from_counts(num_completed=number_completed_games,
                                                             num_deadly_games=len(invites_with_death),
                                                             num_deaths_on_games=len(invites_where_player_died))[0]
        self.save()

    def get_invites_with_death(self, completed_game_invites):
        return [invite for invite in completed_game_invites if invite.relevant_game.at_least_one_death()]

    def get_invites_where_player_died(self, invites_with_death):
        return [invite for invite in invites_with_death if invite.attendance and invite.attendance.is_death()]

    def recompute_gm_title(self):
        self.gm_suffix = self._gm_suffix_from_num_gm_games(self.num_games_gmed)[0]

        # gm_prefix can be None, so we return the db value here
        self.gm_prefix = self._gm_prefix_from_stats(num_gm_games=self.num_games_gmed,
                                                    num_killed_contractors=self.num_gm_kills)
        self.save()

    def completed_game_invites(self):
        return self.user.game_invite_set \
            .exclude(get_completed_game_invite_excludes_query()) \
            .exclude(is_declined=True) \
            .order_by("-relevant_game__end_time") \
            .all()

    def get_avail_improvements(self):
        return self.user.rewarded_player.filter(rewarded_character=None,
                                            is_charon_coin=False).filter(is_void=False).all()

    def get_avail_charon_coins(self):
        return self.user.rewarded_player.filter(rewarded_character=None, is_charon_coin=True).filter(is_void=False).all()

    def get_avail_exp_rewards(self):
        return self.user.experiencereward_set.filter(is_void=False, rewarded_character=None).all()

    def get_games_where_player_gmed(self):
        return Game.objects.filter(gm=self.user).exclude(get_completed_game_excludes_query()) \
                .order_by("-end_time") \
                .all()

    def get_gm_title_tooltip(self):
        return "Games GMed: {}<br>Contractors killed: {}<br>Victories awarded: {} <br>Losses awarded: {}"\
            .format(self.num_games_gmed, self.num_gm_kills, self.num_gm_victories, self.num_gm_losses)

    def _player_prefix_from_counts(self, num_completed, num_deadly_games, num_deaths_on_games):
        if num_completed < 3:
            return PLAYER_PREFIX[0]
        elif num_deadly_games == 0:
            return PLAYER_PREFIX[1]
        less_than_five_deadly_games = num_deadly_games < 5
        death_ratio = num_deaths_on_games / num_deadly_games
        if death_ratio < 0.2:
            # devious
            return PLAYER_PREFIX[4] if less_than_five_deadly_games else PLAYER_PREFIX[7]
        elif death_ratio < 0.6:
            # resourceful
            return PLAYER_PREFIX[3] if less_than_five_deadly_games else PLAYER_PREFIX[6]
        else:
            # unlucky
            return PLAYER_PREFIX[2] if less_than_five_deadly_games else PLAYER_PREFIX[5]


    def _player_suffix_from_num_games(self, num_completed):
        if num_completed < 5:
            return PLAYER_SUFFIX[0]
        elif num_completed < 15:
            return PLAYER_SUFFIX[1]
        elif num_completed < 30:
            return PLAYER_SUFFIX[2]
        elif num_completed < 60:
            return PLAYER_SUFFIX[3]
        else:
            return PLAYER_SUFFIX[4]

    def _gm_suffix_from_num_gm_games(self, num_gm_games):
        if num_gm_games < 1:
            return GM_SUFFIX[0]
        elif num_gm_games < 5:
            return GM_SUFFIX[1]
        elif num_gm_games < 15:
            return GM_SUFFIX[2]
        elif num_gm_games < 50:
            return GM_SUFFIX[3]
        else:
            return GM_SUFFIX[4]

    def _gm_prefix_from_stats(self, num_gm_games, num_killed_contractors):
        if num_gm_games == 0:
            return None
        kill_ratio = num_killed_contractors/num_gm_games
        if kill_ratio < 0.07:
            # pillowy
            return GM_PREFIX[0][0]
        elif kill_ratio < 0.15:
            # benevolent
            return GM_PREFIX[1][0]
        elif kill_ratio < 0.5:
            # just
            return GM_PREFIX[2][0]
        elif kill_ratio < 0.75:
            # Sadistic
            return GM_PREFIX[3][0]
        else:
            # Cruel
            return GM_PREFIX[4][0]
