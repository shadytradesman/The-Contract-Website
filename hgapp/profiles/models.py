from django.db import models
from django.conf import settings

from django.utils import timezone
from games.models import Game, Move, REQUIRED_HIGH_ROLLER_STATUS, REQ_STATUS_ANY, REQ_STATUS_NEWBIE_OR_NOVICE, \
    REQ_STATUS_NEWBIE, REQ_STATUS_NOVICE

from games.games_constants import get_completed_game_invite_excludes_query, get_completed_game_excludes_query
from account.models import EmailAddress

NEWBIE_NOVICE_STATUSES = [
    REQ_STATUS_ANY,
    REQ_STATUS_NEWBIE,
    REQ_STATUS_NOVICE,
    REQ_STATUS_NEWBIE_OR_NOVICE]

UNTESTED = 'UNTESTED'
SHELTERED = 'SHELTERED'
UNLUCKY = 'UNLUCKY'
RESOURCEFUL = 'RESOURCEFUL'
DEVIOUS = 'DEVIOUS'
TORTURED = 'TORTURED'
CALCULATING = 'CALCULATING'
INGENIOUS = 'INGENIOUS'

PLAYER_PREFIX = (
    (UNTESTED, 'Untested'),
    (SHELTERED, 'Sheltered'),
    (UNLUCKY, 'Unlucky'),
    (RESOURCEFUL, 'Resourceful'),
    (DEVIOUS, 'Devious'),
    (TORTURED, 'Tortured'),
    (CALCULATING, 'Calculating'),
    (INGENIOUS, 'Ingenious'),
)

NEWBIE = 'NEWBIE'
NOVICE = 'NOVICE'
ADEPT = 'ADEPT'
SEASONED = 'SEASONED'
PROFESSIONAL = 'PROFESSIONAL'
VETERAN = 'VETERAN'
MASTER = 'MASTER'
GRANDMASTER = 'GRANDMASTER'
LEGEND = 'LEGEND'
PLAYER_SUFFIX = (
    (NEWBIE, 'Newbie'),
    (NOVICE, 'Novice'),
    (ADEPT, 'Adept'),
    (PROFESSIONAL, 'Professional'),
    (VETERAN, 'Veteran'),
    (SEASONED, 'Operative'),
    (MASTER, 'Master'),
    (GRANDMASTER, 'Grandmaster'),
    (LEGEND, 'Legend'),
)

GM_PREFIX = (
    ('PILLOW', 'Pillow'),
    ('BENEVOLENT', 'Benevolent'),
    ('JUST', 'Just'),
    ('SADISTIC', 'Sadistic'),
    ('CRUEL', 'Cruel'),
)

SPECTATOR = 'SPECTATOR'
REFEREE = 'REFEREE'
BOSS = 'BOSS'
RULER = 'RULER'
GOD = 'GOD'
HARBINGER = 'HARBINGER'
MIDDLE_MANAGEMENT = 'MIDDLE_MANAGEMENT'
PSYCHO = 'PSYCHO'
GM_SUFFIX = (
    (SPECTATOR, 'Spectator'),
    (REFEREE, 'Referee'),
    (BOSS, 'Boss'),
    (RULER, 'Ruler'),
    (GOD, 'God'),
    (HARBINGER, 'Harbinger'),
    (MIDDLE_MANAGEMENT, 'Manager'),
    (PSYCHO, 'Psycho')
)


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE)
    about = models.TextField(max_length=10000, blank=True)
    confirmed_agreements = models.BooleanField(default=False)
    able_to_port = models.BooleanField(default=False)
    ps2_user = models.BooleanField(default=False)
    early_access_user = models.BooleanField(default=False)
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

    num_games_gmed = models.IntegerField(default=0)
    num_games_gmed_novice = models.IntegerField(default=0)
    num_moves_gmed = models.IntegerField(default=0)
    num_gm_kills = models.IntegerField(default=0)
    num_gm_victories = models.IntegerField(default=0)
    num_gm_losses = models.IntegerField(default=0)
    num_gm_kills_novice = models.IntegerField(default=0)
    num_gm_victories_novice = models.IntegerField(default=0)
    num_gm_losses_novice = models.IntegerField(default=0)
    num_golden_ratios = models.IntegerField(default=0)
    num_gmed_players = models.IntegerField(default=0)
    num_gmed_cells = models.IntegerField(default=0)
    num_gmed_contractors = models.IntegerField(default=0)

    num_player_games = models.IntegerField(default=0)
    num_player_games_novice = models.IntegerField(default=0)
    num_player_victories = models.IntegerField(default=0)
    num_player_losses = models.IntegerField(default=0)
    num_player_deaths = models.IntegerField(default=0)
    num_played_ringers = models.IntegerField(default=0)
    num_contractors_played = models.IntegerField(default=0)
    num_deadly_player_games = models.IntegerField(default=0)
    num_player_survivals = models.IntegerField(default=0)

    view_adult_content = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    date_set_adult_content = models.DateTimeField(blank=True, null=True)

    # Email prefs
    contract_invitations = models.BooleanField(default=True)
    contract_updates = models.BooleanField(default=True)
    direct_messages = models.BooleanField(default=True)
    intro_contracts = models.BooleanField(default=True)
    site_announcements = models.BooleanField(default=True)

    # Other Preferences
    hide_fake_ads = models.BooleanField(default=False)

    # Scenario Exchange
    exchange_contributor = models.BooleanField(default=False)
    exchange_approver = models.BooleanField(default=False)
    exchange_credits = models.IntegerField(default=0)

    def __str__(self):
        return self.user.username

    class Meta:
        indexes = [
            models.Index(fields=['num_games_gmed']),
            models.Index(fields=['num_gm_kills']),
            models.Index(fields=['num_gmed_players']),
            models.Index(fields=['num_player_games']),
            models.Index(fields=['num_played_ringers']),
            models.Index(fields=['num_player_survivals']),
            models.Index(fields=['num_moves_gmed']),
        ]

    def player_can_view(self, player):
        if player == self.user or player.is_superuser:
            return True
        if self.is_private:
            members = set()
            for cell in self.user.cell_set.all():
                members = members.union(set(cell.members.values_list("pk", flat=True)))
            return player.pk in members
        else:
            return True

    def get_confirmed_email(self):
        email = EmailAddress.objects.get_primary(self.user)
        is_verified = email and email.verified
        if is_verified:
            return email
        else:
            return None

    def get_primary_email(self):
        return EmailAddress.objects.get_primary(self.user)

    # This should be the only way you set the user's adult content prefs
    def update_view_adult_content(self, view_adult_content):
        if view_adult_content != self.view_adult_content:
            self.view_adult_content = view_adult_content
            self.date_set_adult_content = timezone.now()
            self.save()

    def update_move_stat(self):
        self.num_moves_gmed = self.get_moves_where_player_gmed().count()
        self.save()

    def update_gm_stats(self):
        gm_games = self.get_games_where_player_gmed()
        num_gm_games = gm_games.count()
        num_gm_games_novice = 0
        num_gm_kills = 0
        num_gm_victories = 0
        num_gm_losses = 0
        num_gm_kills_novice = 0
        num_gm_victories_novice = 0
        num_gm_losses_novice = 0
        num_golden_ratio_games = 0
        cells_gmed = set()
        contractors_gmed = set()
        players_gmed = set()
        for game in gm_games:
            game_kills = game.number_deaths()
            game_victories = game.number_victories()
            game_losses = game.number_losses()
            if game.required_character_status in NEWBIE_NOVICE_STATUSES:
                num_gm_kills_novice = num_gm_kills_novice + game_kills
                num_gm_victories_novice = num_gm_victories_novice + game_victories
                num_gm_losses_novice = num_gm_losses_novice + game_losses
                num_gm_games_novice = num_gm_games_novice + 1
            num_gm_kills = num_gm_kills + game_kills
            num_gm_victories = num_gm_victories + game_victories
            num_gm_losses = num_gm_losses + game_losses
            if game.achieves_golden_ratio():
                num_golden_ratio_games = num_golden_ratio_games + 1
            if game.cell:
                cells_gmed.add(game.cell.id)
            for attendance in game.game_attendance_set.all():
                if attendance.attending_character:
                    contractors_gmed.add(attendance.attending_character.id)
                    players_gmed.add(attendance.attending_character.player.id)
        self.num_gmed_players = len(players_gmed)
        self.num_gmed_contractors = len(contractors_gmed)
        self.num_gmed_cells = len(cells_gmed)
        self.num_games_gmed = num_gm_games
        self.num_moves_gmed = self.get_moves_where_player_gmed().count()
        self.num_gm_losses = num_gm_losses
        self.num_gm_kills = num_gm_kills
        self.num_gm_victories = num_gm_victories_novice
        self.num_gm_losses_novice = num_gm_losses_novice
        self.num_gm_kills_novice = num_gm_kills_novice
        self.num_gm_victories_novice = num_gm_victories_novice
        self.num_games_gmed_novice = num_gm_games_novice
        self.num_golden_ratios = num_golden_ratio_games
        self.save()

    def can_view_adult(self):
        return self.view_adult_content

    def recompute_titles(self):
        self.update_gm_stats()
        self.update_player_stats()
        self.recompute_player_title()
        self.recompute_gm_title()

    def update_player_stats(self):
        completed_game_invites = self.completed_game_invites()
        self.num_player_games = completed_game_invites.count()
        invites_with_death = self.get_invites_with_death(completed_game_invites)
        self.num_deadly_player_games = len(invites_with_death)
        self.num_player_games_novice = self._get_novice_game_count(completed_game_invites)
        played_character_ids = set()
        num_deaths = 0
        num_victories = 0
        num_losses = 0
        num_played_ringers = 0
        for invite in completed_game_invites:
            if invite.attendance:
                if invite.attendance.attending_character:
                    played_character_ids.add(invite.attendance.attending_character.id)
                else:
                    num_played_ringers = num_played_ringers + 1
                if invite.attendance.is_victory():
                    num_victories = num_victories + 1
                elif invite.attendance.is_loss():
                    num_losses = num_losses + 1
                elif invite.attendance.is_death():
                    num_deaths = num_deaths + 1
        self.num_contractors_played = len(played_character_ids)
        self.num_player_deaths = num_deaths
        self.num_player_victories = num_victories
        self.num_player_losses = num_losses
        self.num_played_ringers = num_played_ringers
        self.num_player_survivals = self.num_deadly_player_games - num_deaths
        self.save()


    def recompute_player_title(self):
        self.player_suffix = self._player_suffix_from_num_games(self.num_player_games)
        # Player prefix is calculated based on any/newbie/novice contracts because they expect higher death counts.
        self.player_prefix = self._player_prefix_from_counts(num_completed=self.num_player_games_novice,
                                                             num_deadly_games=self.num_deadly_player_games,
                                                             num_deaths_on_games=self.num_player_deaths)
        self.save()

    # Return invites for games that are completed where the player played a contractor and another contractor died.
    def get_invites_with_death(self, completed_game_invites):
        return [invite for invite in completed_game_invites
                if invite.attendance
                and invite.attendance.attending_character
                and invite.relevant_game.at_least_one_death()]

    def get_invites_where_player_died(self, invites_with_death):
        return [invite for invite in invites_with_death if invite.attendance and invite.attendance.is_death()]

    def recompute_gm_title(self):
        self.gm_suffix = self._gm_suffix_from_num_gm_games(self.num_games_gmed, self.num_moves_gmed)

        # gm_prefix can be None, so we return the db value here
        # GM prefix is calculated based on any/newbie/novice contracts because they expect higher death counts.
        self.gm_prefix = self._gm_prefix_from_stats(num_gm_games=self.num_games_gmed_novice,
                                                    num_killed_contractors=self.num_gm_kills)
        self.save()

    def get_gm_title(self):
        if self.gm_prefix:
            return "{} {}".format(self.get_gm_prefix_display(), self.get_gm_suffix_display())
        else:
            return self.get_gm_suffix_display()

    def completed_game_invites(self):
        return self.user.game_invite_set \
            .exclude(get_completed_game_invite_excludes_query()) \
            .exclude(is_declined=True) \
            .prefetch_related("attendance", "attendance__attending_character") \
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
                .prefetch_related("game_attendance_set") \
                .order_by("-end_time") \
                .all()

    def get_moves_where_player_gmed(self):
        return Move.objects.filter(gm=self.user).exclude(deleted_on__isnull=False).order_by("-created_date").all()

    def get_gm_title_tooltip(self):
        return "Contracts GMed: {}<br>Contractors killed: {}<br>Victories awarded: {} <br>Losses awarded: {}"\
            .format(self.num_games_gmed, self.num_gm_kills, self.num_gm_victories, self.num_gm_losses)

    def _player_prefix_from_counts(self, num_completed, num_deadly_games, num_deaths_on_games):
        if num_completed < 3:
            return UNTESTED
        game_deadliness = num_deadly_games/num_completed
        if num_deadly_games == 0 or game_deadliness < 0.07:
            # fewer than 1 in 14 games has PC death
            return SHELTERED
        # fewer than 1 in 6 games has PC death or hasn't been in 5 games where a Contractor died
        rarely_plays_in_deadly_games = game_deadliness < .16 or num_deadly_games < 5
        death_ratio = num_deaths_on_games / num_deadly_games
        if death_ratio < 0.2:
            return DEVIOUS if rarely_plays_in_deadly_games else INGENIOUS
        elif death_ratio < 0.5:
            return RESOURCEFUL if rarely_plays_in_deadly_games else CALCULATING
        else:
            return UNLUCKY if rarely_plays_in_deadly_games else TORTURED


    def _player_suffix_from_num_games(self, num_completed):
        if num_completed < 5:
            return NEWBIE
        elif num_completed < 15:
            return NOVICE
        elif num_completed < 30:
            return ADEPT
        elif num_completed < 60:
            return SEASONED
        elif num_completed < 100:
            return PROFESSIONAL
        elif num_completed < 200:
            return VETERAN
        elif num_completed < 350:
            return MASTER
        elif num_completed < 500:
            return GRANDMASTER
        else:
            return LEGEND


    def _gm_suffix_from_num_gm_games(self, num_games_gmed, num_moves_gmed):
        num_gm_games = num_games_gmed + (0.25 * num_moves_gmed)
        if num_gm_games < 1:
            return SPECTATOR
        elif num_gm_games < 5:
            return REFEREE
        elif num_gm_games < 15:
            return MIDDLE_MANAGEMENT
        elif num_gm_games < 30:
            return BOSS
        elif num_gm_games < 60:
            return RULER
        elif num_gm_games < 100:
            return HARBINGER
        elif num_gm_games < 200:
            return GOD
        else:
            return PSYCHO


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


    def _get_novice_game_count(self, completed_game_invites):
        count = 0
        for invite in completed_game_invites:
            if invite.relevant_game.required_character_status in NEWBIE_NOVICE_STATUSES:
                count = count + 1
        return count


