import logging

from django.db import models
from django.db.models import Count
from django.conf import settings
from django.forms.models import model_to_dict
from django.db.models import Q
from django.contrib.auth import get_user_model

from characters.models import Character, HIGH_ROLLER_STATUS, Character_Death, ExperienceReward, AssetDetails, EXP_GM, \
    EXP_LOSS_V3, EXP_WIN_V3, EXP_LOSS_RINGER_V2, EXP_WIN_RINGER_V2, EXP_LOSS_IN_WORLD_V2, EXP_WIN_IN_WORLD_V2, EXP_MVP,\
    EXP_WIN_V1, EXP_LOSS_V1, Artifact, EXP_GM_MOVE_V2, EXP_GM_RATIO, EXP_GM_NEW_PLAYER, StockWorldElement, ELEMENT_TYPE, \
    CONDITION, CIRCUMSTANCE, TROPHY, LOOSE_END, STATUS_ANY, EXP_EXCHANGE, HIGH_ROLLER_STATUS, SEASONED_PORTED, \
    VETERAN_PORTED, STATUS_NEWBIE, STATUS_NOVICE, STATUS_SEASONED, STATUS_PROFESSIONAL, STATUS_VETERAN
from django.template.loader import render_to_string
from powers.models import Power, Power_Full
from cells.models import Cell, WorldEvent, CellMembership
from django.utils import timezone
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup
from .games_constants import EXP_V1_V2_GAME_ID
from guardian.shortcuts import assign_perm

from django.urls import reverse
from django.utils.safestring import SafeText
from games.games_constants import GAME_STATUS, get_completed_game_excludes_query, get_scheduled_game_excludes_query
from characters.templatetags.character_game_tags import render_scenario_element
from characters.signals import recalculate_stats
from functools import reduce

from hgapp.utilities import get_object_or_none
import django.dispatch
from notifications.models import Notification, REWARD_NOTIF, CONTRACTOR_NOTIF, SCENARIO_NOTIF


NotifyGameInvitee = django.dispatch.Signal() # providing_args=['game_invite', 'request']
GameChangeStartTime = django.dispatch.Signal() # providing_args=['game', 'request']
GameEnded = django.dispatch.Signal() # providing_args=['game', 'request']

EXCHANGE_SUBMISSION_VALUE = 340
EXCHANGE_SCENARIO_COST = 100


logger = logging.getLogger("app." + __name__)


REQ_STATUS_VETERAN = 'VETERAN'
REQ_STATUS_PROFESSIONAL = 'PROFESSIONAL'
REQ_STATUS_SEASONED = 'SEASONED'
REQ_STATUS_NOVICE = 'NOVICE'
REQ_STATUS_NEWBIE = 'NEWBIE'
REQ_STATUS_NEWBIE_OR_NOVICE = 'NEWBIE_OR_NOVICE'
REQ_STATUS_ANY = 'ANY'
REQUIRED_HIGH_ROLLER_STATUS = (
    (REQ_STATUS_ANY, 'Any'),
    (REQ_STATUS_NEWBIE_OR_NOVICE, 'Newbie or Novice'),
    (REQ_STATUS_NEWBIE, 'Newbie'),
    (REQ_STATUS_NOVICE, 'Novice'),
    (REQ_STATUS_SEASONED, 'Seasoned'),
    (REQ_STATUS_PROFESSIONAL, 'Professional'),
    (REQ_STATUS_VETERAN, 'Veteran'),
)

WIN = 'WIN'
LOSS = 'LOSS'
DEATH = 'DEATH'
DECLINED = 'DECLINED'
RINGER_VICTORY = 'RINGER_VICTORY'
RINGER_FAILURE = 'RINGER_FAILURE'
OUTCOME = (
    (WIN, 'Victory'),
    (LOSS, 'Loss'),
    (DEATH, 'Died'),
    (DECLINED, 'Declined Harbinger Invite'),
    (RINGER_VICTORY, 'Ringer Victory'),
    (RINGER_FAILURE, 'Ringer Failure'),
)

WIKI_EDIT_ALL = 'ALL'
WIKI_EDIT_EXCHANGE = 'EXCHANGE'
WIKI_EDIT_MODE = (
    (WIKI_EDIT_ALL, 'Anyone spoiled'),
    (WIKI_EDIT_EXCHANGE, 'Scenario Exchange contributors')
)

DISCOVERY_PURCHASED = "PURCHASED"
DISCOVERY_REASON = (
    ('PLAYED', 'Played'),
    ('CREATED', 'Created'),
    ('SHARED', 'Shared'),
    ('UNLOCKED', 'Unlocked'),
    (DISCOVERY_PURCHASED, 'Purchased'),
)

INVITE_ONLY = 'INVITE_ONLY'
WORLD_MEMBERS = 'WORLD_MEMBERS'
ANYONE = 'ANYONE'
CLOSED = 'CLOSED'
INVITE_MODE = (
    (INVITE_ONLY, 'Invited Players Only'),
    (WORLD_MEMBERS, 'Playgroup Members Only'),
    (ANYONE, 'Any Player'),
    (CLOSED, 'Closed for RSVPs'),
)

OVERVIEW = "OVERVIEW"
BACKSTORY = "BACKSTORY"
INTRODUCTION = "INTRODUCTION"
MISSION = "MISSION"
AFTERMATH = "AFTERMATH"
WRITEUP_SECTION = (
    (OVERVIEW, "Overview"),
    (BACKSTORY, "Backstory"),
    (INTRODUCTION, "Intro and Briefing"),
    (MISSION, "Mission"),
    (AFTERMATH, "Aftermath"),
)


NOTIF_VAR_UPCOMING = "upcoming"
NOTIF_VAR_FINISHED = "finished"


APPROVED = 'APPROVED'
REJECTED = 'REJECTED'
WAITING = 'WAITING'
WITHDRAWN = 'WITHDRAWN' # withdrawn before approval
REMOVED = 'REMOVED' # removed from exchange
APPROVAL_STATUS = (
    (APPROVED, 'Approved'),
    (REJECTED, 'Rejected'),
    (WAITING, 'Awaiting Approval'),
    (WITHDRAWN, 'Withdrawn'),
    (REMOVED, 'Removed'),
)

def migrate_add_gms(apps, schema_editor):
    Game = apps.get_model('games', 'Game')
    for game in Game.objects.all().iterator():
        game.gm = game.creator
        game.save()


def reverse_add_gms_migration(apps, schema_editor):
    pass


class Game(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='game_creator',
        on_delete=models.PROTECT)
    gm = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='game_gm',
        on_delete=models.PROTECT)
    scenario = models.ForeignKey(
        "Scenario",
        on_delete=models.PROTECT)
    required_character_status = models.CharField(choices=REQUIRED_HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=REQ_STATUS_ANY)
    title = models.CharField(max_length=130)
    created_date = models.DateTimeField('date created',
                                        auto_now_add=True)
    scheduled_start_time = models.DateTimeField('scheduled start time',
                                                null=True,
                                                blank=True)
    actual_start_time = models.DateTimeField('actual start time',
                                            null=True,
                                            blank=True)
    end_time = models.DateTimeField('end time',
                                    null=True,
                                    blank=True)
    status = models.CharField(choices=GAME_STATUS,
                              max_length=25,
                              default=GAME_STATUS[0])
    attended_by = models.ManyToManyField(Character,
                                         through="Game_Attendance",
                                         through_fields=('relevant_game','attending_character'))
    invitations = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         through="Game_Invite")
    scenario_notes = models.TextField(max_length=10000,
                                      null=True,
                                      blank=True)
    cell = models.ForeignKey(Cell,
                             null=True, # for migration reasons. All games should have cells.
                             blank=True, # for migration reasons. All games should have cells.
                             on_delete=models.CASCADE)
    gm_experience_reward = models.OneToOneField(ExperienceReward,
                                          null=True,
                                          blank=True,
                                          on_delete=models.CASCADE)
    last_email_date = models.DateTimeField('last_email_date', null=True, auto_now_add=True)

    # Invitation stuff
    hook = models.TextField(max_length=7000,
                            null=True,
                            blank=True)
    open_invitations = models.BooleanField(default=True) # deprecated. Use invitation_mode instead.
    is_nsfw = models.BooleanField(default=False)
    list_in_lfg = models.BooleanField(default=False)
    invite_all_members = models.BooleanField(default=False)
    allow_ringers = models.BooleanField(default=False)
    invitation_mode = models.CharField(choices=INVITE_MODE, max_length=55, default=INVITE_MODE[0][0])
    gametime_url = models.CharField(max_length=2500, blank=True, null=True)
    max_rsvp = models.IntegerField(blank=True, null=True)
    mediums = models.ManyToManyField("GameMedium",
                                     blank=True)

    class Meta:
        permissions = (
            ('edit_game', 'Edit game'),
        )

    def save(self, *args, **kwargs):
        if not hasattr(self, 'gm'):
            self.gm = self.creator
        if not hasattr(self, 'scenario') or not self.scenario:
            scenario = Scenario(creator=self.gm,
                                title=str(self.title),
                                description="Put the details of the Scenario here",
                                suggested_status=STATUS_ANY,
                                max_players=5,
                                min_players=2)
            scenario.save()
            writeup = ScenarioWriteup(writer=self.gm,
                                      relevant_scenario=scenario,
                                      content="Put the details of the Scenario here",
                                      section=MISSION)
            writeup.save()
            self.scenario = scenario
        if self.pk is None:
            super(Game, self).save(*args, **kwargs)
            assign_perm('view_game', self.creator, self)
            assign_perm('view_game', self.gm, self)
            assign_perm('edit_game', self.creator, self)
        else:
            super(Game, self).save(*args, **kwargs)

    def __str__(self):
        return "[" + self.status + "] " + self.scenario.title + " run by: " + self.gm.username

    def player_can_edit(self, player):
        if player.is_superuser:
            return True
        return player.is_authenticated and (player.has_perm('edit_game', self) \
                                            or (self.cell is not None and self.cell.player_can_manage_games(player)))

    def render_timeline_display(self, user, variety):
        if variety == NOTIF_VAR_UPCOMING:
            return render_to_string("games/timeline/timeline_upcoming_game.html", {
                "game": self,
                "user": user,
                "my_invitation": get_object_or_none(user.game_invite_set.filter(relevant_game=self.pk))})
        if variety == NOTIF_VAR_FINISHED:
            game = Game.objects.prefetch_related('game_invite_set__attendance').get(pk=1)
            return render_to_string("games/timeline/timeline_completed_game.html", {"game": game})
        raise ValueError("invalid variety of game timeline: " + variety)


    def render_timeline_header(self, user, variety):
        if variety == NOTIF_VAR_UPCOMING:
            if not self.is_scheduled():
                return mark_safe("Invitations closed")
            else:
                return "You've been invited to join a Contract"
        if variety == NOTIF_VAR_FINISHED:
            return "{} ran {}".format(self.gm.username, self.scenario.title)
        raise ValueError("invalid variety of game timeline: " + variety)

    def invite_instructions(self):
        if self.invitation_mode == CLOSED:
            return "Edit the Game to open it for RSVPs."
        if self.invitation_mode == INVITE_ONLY:
            return "Invite Players using the form below."
        if self.invitation_mode == WORLD_MEMBERS:
            return "Simply share this page with any Playgroup members you wish to invite, or invite any Player using the form below."
        else:
            return "Simply share this page with any Player you wish to invite."

    def player_can_rsvp(self, player):
        return not self.reason_player_cannot_rsvp(player)

    def get_accepted_invites(self):
        return self.game_invite_set.filter(is_declined=False, attendance__isnull=False).all()

    def get_open_invites(self):
        return self.game_invite_set.select_related("attendance").filter(attendance__isnull=True).select_related("invited_player__profile").all()

    def reason_player_cannot_rsvp(self, player):
        if not player.is_authenticated or player.is_anonymous:
            return "You must log in to accept this Contract invite."
        if self.gm == player:
            return "GMs cannot RSVP to their own Contracts."
        if player.is_superuser:
            return None
        if hasattr(self, "max_rsvp") and self.max_rsvp and self.get_attended_players().count() >= self.max_rsvp:
            if player not in [x for x in self.get_attended_players()]:
                return "This Contract is full."
        if self.invitation_mode == CLOSED or not self.is_scheduled():
            return "This Contract is closed for RSVPs."
        if self.is_nsfw and not player.profile.view_adult_content:
            return "This Contract is marked for adults. Your content settings do not allow you to participate."
        player_invitation = get_object_or_none(player.game_invite_set.filter(relevant_game=self.id))
        if player_invitation:
            return None
        if self.invitation_mode == INVITE_ONLY:
            return "This Contract only allows those with an invitation to RSVP."
        if self.invitation_mode == WORLD_MEMBERS:
            membership = self.cell.get_player_membership(player)
            if not membership:
                return "This Contract only allows those who are a member of its Playgroup to RSVP without an invite."
            if membership and membership.is_banned:
                return "You are banned from this Playgroup."
            else:
                return None
        # ANYONE case
        return None

    def get_webhook_post(self, request, is_changed_start):
        if is_changed_start:
            format_string = "{} has updated the start time of their Contract - **{}** for **{}** Contractors in {}. The Contract *now* starts at <t:{}:f> (<t:{}:R>). RSVP: {}"
        else:
            format_string = "{} will run **{}** for **{}** Contractors in {}. The Contract starts at <t:{}:f> (<t:{}:R>). RSVP: {}"
        return format_string.format(
            self.gm.username,
            self.scenario.title,
            self.get_required_character_status_display(),
            self.cell.name,
            int(self.scheduled_start_time.timestamp()),
            int(self.scheduled_start_time.timestamp()),
            request.build_absolute_uri(reverse('games:games_view_game', args=(self.id,)))
        )

    def get_header_display(self):
        if self.is_scheduled():
            return "Upcoming Contract"
        if self.is_active():
            return "Ongoing Contract"
        if self.is_canceled():
            return "Canceled Contract"
        return "Completed Contract"

    def is_scheduled(self):
        return self.status == GAME_STATUS[0][0]

    def is_active(self):
        return self.status == GAME_STATUS[1][0]

    def is_finished(self):
        return self.status == GAME_STATUS[2][0]

    def is_archived(self):
        return self.status == GAME_STATUS[3][0]

    def is_canceled(self):
        return self.status == GAME_STATUS[4][0]

    def is_void(self):
        return self.status == GAME_STATUS[5][0]

    def is_recorded(self):
        return self.status == GAME_STATUS[6][0]

    def transition_to_canceled(self):
        assert(self.is_scheduled() or self.is_active())
        self.status = GAME_STATUS[4][0]
        self.save()
        for game_invite in self.game_invite_set.all():
            game_invite.delete()
        for game_attendance in self.game_attendance_set.all():
            game_attendance.delete()

    def transition_to_active(self):
        assert(self.is_scheduled())
        for invite in self.game_invite_set.all():
            if not invite.attendance:
                invite.delete()
        self.status = GAME_STATUS[1][0]
        self.actual_start_time = timezone.now()
        self.save()

    # Attendances should be saved by this point.
    def transition_to_finished(self):
        assert(self.is_active())
        for character in self.attended_by.all():
            character.highlight_crafting = True
            character.save()
            character.default_perms_char_and_powers_to_player(self.gm)
        if hasattr(self, "cell") and self.cell:
            self.cell.find_world_date = timezone.now()
        self.status = GAME_STATUS[2][0]
        self.end_time = timezone.now()
        self.save()
        self.give_rewards()
        self.update_profile_stats()
        self.unlock_stock_scenarios()
        self.progress_loose_ends()

    def progress_loose_ends(self):
        for character in self.attended_by.all():
            character.progress_loose_ends(self.actual_start_time)


    def is_introductory_game(self):
        # Returns True if this Game had at least one new Player in it.
        attending_invites = self.get_attended_players()
        for invite in attending_invites:
            if invite.profile.completed_game_invites().count() == 1:
                return True
        return False

    def give_rewards(self):
        if not self.is_finished() and not self.is_recorded():
            raise ValueError("Game tried to grant rewards but is not completed: " + str(self.pk))
        for game_attendance in self.game_attendance_set.all():
            game_attendance.give_reward()
        gm_reward = Reward(relevant_game=self,
                           rewarded_player=self.gm,
                           is_improvement=True,
                           is_gm_reward=True)
        gm_reward.save()
        if self.achieves_golden_ratio() and self.cell and self.cell.use_golden_ratio:
            self._grant_gm_exp_reward(EXP_GM_RATIO)
        elif self.is_introductory_game():
            self._grant_gm_exp_reward(EXP_GM_NEW_PLAYER)
        self.scenario.grant_or_void_reward_as_necessary()

    def _grant_gm_exp_reward(self, reward_type):
        if self.gm_experience_reward and not self.gm_experience_reward.is_void:
            raise ValueError("Game is granting exp reward to gm when it already has one.", str(self.id))
        exp_reward = ExperienceReward(
            rewarded_player=self.gm,
            type=reward_type
        )
        exp_reward.save()
        self.gm_experience_reward = exp_reward
        self.save()

    def recalculate_gm_reward(self):
        current_exp_reward = self.gm_experience_reward
        now_achieves_ratio = self.achieves_golden_ratio()
        should_have_ratio_reward = now_achieves_ratio and self.cell and self.cell.use_golden_ratio
        if should_have_ratio_reward:
            if current_exp_reward and current_exp_reward.type == EXP_GM_NEW_PLAYER:
                current_exp_reward.mark_void()
                self._grant_gm_exp_reward(EXP_GM_RATIO)
            if not current_exp_reward:
                self._grant_gm_exp_reward(EXP_GM_RATIO)
            return
        if not should_have_ratio_reward:
            if current_exp_reward and current_exp_reward.type == EXP_GM_RATIO:
                current_exp_reward.mark_void()
        if self.is_introductory_game():
            if not current_exp_reward or current_exp_reward.is_void:
                self._grant_gm_exp_reward(EXP_GM_NEW_PLAYER)

    # Determines if the game's golden ratio status has changed
    def recalculate_golden_ratio(self, original_value):
        current_value = self.achieves_golden_ratio()
        if current_value != original_value:
            if current_value and self.cell and self.cell.use_golden_ratio:
                if hasattr(self, "gm_experience_reward") and self.gm_experience_reward:
                    self.gm_experience_reward.mark_void()
                self._grant_gm_exp_reward(EXP_GM_RATIO)
        return current_value

    def achieves_golden_ratio(self):
        death = False
        win = False
        for attendance in self.game_attendance_set.all():
            if attendance.is_victory():
                win = True
            if attendance.is_death():
                death = True
        return win and death

    def at_least_one_death(self):
        for attendance in self.game_attendance_set.all():
            if attendance.is_death():
                return True

    def number_deaths(self):
        num_deaths = 0
        for attendance in self.game_attendance_set.all():
            if attendance.is_death():
                num_deaths = num_deaths + 1
        return num_deaths

    def number_victories(self):
        number_victories = 0
        for attendance in self.game_attendance_set.all():
            if attendance.is_victory():
                number_victories = number_victories + 1
        return number_victories

    def number_losses(self):
        num_losses = 0
        for attendance in self.game_attendance_set.all():
            if attendance.is_loss():
                num_losses = num_losses + 1
        return num_losses

    def get_attended_players(self):
        return self.invitations.filter(game_invite__is_declined=False, game_invite__attendance__isnull=False).all()

    def get_journaled_attendances(self):
        return self.game_attendance_set.filter(is_confirmed=True, journal__isnull=False, journal__is_downtime=False).all()

    def not_attending(self, player):
        invite = get_object_or_none(self.game_invite_set.filter(invited_player=player))
        if invite:
            attendance = invite.attendance
            if attendance:
                attendance.delete()
            invite.delete()

    def get_gm_reward(self):
        return self.reward_set.filter(is_void=False, rewarded_player=self.gm).first()

    def get_status_blurb(self):
        if self.is_scheduled():
            return "This game is Scheduled to start " + self.scheduled_start_time.strftime('on %d, %b %Y at %I:%M %Z')
        if self.is_active():
            return "This game is Active and started " + self.actual_start_time.strftime('on %d, %b %Y at %I:%M %Z')
        if self.is_canceled():
            return "This game was Canceled and never took place."
        return "This game is " + self.get_status_display() + " and ended " + self.end_time.strftime('on %d, %b %Y at %I:%M %Z')

    def player_participated(self, player):
        return self.gm == player or self.game_invite_set.filter(is_declined=False, invited_player=player).first()

    def update_participant_titles(self):
        self.gm.profile.recompute_titles()
        for invite in self.invitations.all():
            invite.profile.recompute_titles()
        for character in self.attended_by.all():
            recalculate_stats.send(sender=character.__class__, character_pk=character.pk, is_game=True)

    def update_profile_stats(self):
        self.update_cell_membership_activity()
        self.update_participant_titles()
        if hasattr(self, "cell") and self.cell:
            self.cell.update_safety_stats()
        self.scenario.update_stats()

    def update_cell_membership_activity(self):
        gm_membership = CellMembership.objects.filter(member_player=self.gm).filter(relevant_cell=self.cell).first()
        if gm_membership and self.end_time:
            if gm_membership.last_activity < self.end_time:
                gm_membership.last_activity = self.end_time
                gm_membership.save()
        for invite in self.game_invite_set.filter(attendance__isnull=False).all():
            invited_membership = CellMembership.objects.filter(member_player=invite.invited_player).filter(relevant_cell=self.cell).first()
            if invited_membership and self.end_time:
                if invited_membership.last_activity < self.end_time:
                    invited_membership.last_activity = self.end_time
                    invited_membership.save()

    def unlock_stock_scenarios(self):
        if not self.is_finished() and not self.is_recorded():
            print("Game is not finished: " + str(self.id))
            return
        run_contract_scenarios = Scenario.objects.filter(tags__slug="gm-contract").all()
        for scenario in run_contract_scenarios:
            scenario.unlocked_discovery(self.gm)
        die_in_contract_scenarios = Scenario.objects.filter(tags__slug="die").all()
        play_in_contract_scenarios = Scenario.objects.filter(tags__slug="play-contractor").all()
        for game_attendance in self.game_attendance_set.all():
            if game_attendance.is_confirmed:
                player = game_attendance.get_player()
                if player:
                    for scenario in play_in_contract_scenarios:
                        scenario.unlocked_discovery(player)
                if game_attendance.is_death():
                    for scenario in die_in_contract_scenarios:
                        scenario.unlocked_discovery(player)



class Game_Attendance(models.Model):
    # set to null when ringer.
    attending_character = models.ForeignKey(Character,
                                            null=True,
                                            blank=True,
                                            on_delete=models.PROTECT)
    relevant_game = models.ForeignKey(Game,
                                      on_delete=models.PROTECT)
    notes = models.TextField(max_length=500,
                             null=True,
                             blank=True)
    outcome = models.CharField(choices=OUTCOME,
                               max_length=20,
                               null=True,
                               blank=True)
    character_death = models.OneToOneField(Character_Death,
                                           null=True,
                                           blank=True,
                                           on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=True)
    experience_reward = models.OneToOneField(ExperienceReward,
                                          null=True,
                                          blank=True,
                                          on_delete=models.SET_NULL)
    is_mvp = models.BooleanField(default=False)
    mvp_reward = models.OneToOneField(ExperienceReward,
                                      related_name='mvp_exp_attendance',
                                      null=True,
                                      blank=True,
                                      on_delete=models.SET_NULL)

    def __str__(self):
        return "{} attending {} [{}]".format(self.attending_character.name if self.attending_character else "__",
                                             self.relevant_game.scenario.title,
                                             self.get_outcome_display())

    def is_victory(self):
        return self.outcome == WIN

    def is_loss(self):
        return self.outcome == LOSS

    def is_death(self):
        return self.outcome == DEATH

    def is_ringer_victory(self):
        return self.outcome == RINGER_VICTORY

    def is_ringer_failure(self):
        return self.outcome == RINGER_FAILURE

    def is_declined_invite(self):
        return self.outcome == DECLINED

    def associated_character_reward(self):
        if self.attending_character:
            return self.attending_character.reward_set.filter(relevant_game=self.relevant_game.id).filter(is_void=False).first()
        else:
            return None

    def confirm_and_reward(self):
        self.is_confirmed = True
        self.save()
        self.give_reward()

    def get_rewards(self):
        return Reward.objects.filter(rewarded_player=self.get_player(), relevant_game=self.relevant_game, is_void=False, is_journal=False, is_questionnaire=False).all()

    def get_player(self):
        if self.attending_character:
            return self.attending_character.player
        elif hasattr(self, "game_invite"):
            return self.game_invite.invited_player
        else:
            # this should only occur when initially saving an attendance (before invite is associated with it)
            return None

    # Changes the outcome of the GameAttendance. Handles Gifts, Experience Rewards, attending Character, Character death
    # status, and confirmation status. This method does NOT update the Game's GM rewards (golden ratio or new player).
    def change_outcome(self, new_outcome, is_confirmed, attending_character=None, is_mvp=False):
        current_outcome = self.outcome
        if current_outcome == new_outcome and attending_character == self.attending_character and self.is_confirmed == is_confirmed and self.is_mvp == is_mvp:
            return
        current_rewards = self.get_rewards()
        # Void rewards
        for current_reward in current_rewards:
            current_reward.mark_void()
        # Void experience rewards
        if hasattr(self, "experience_reward") and self.experience_reward:
            self.experience_reward.mark_void()
            self.experience_reward = None
        if hasattr(self, "mvp_reward") and self.mvp_reward:
            self.mvp_reward.mark_void()
            self.mvp_reward = None
        # Void deaths
        if hasattr(self, "character_death") and self.character_death:
            self.character_death.mark_void()
            self.character_death = None
        # If it's a ringer outcome, unassign character
        if new_outcome == RINGER_VICTORY or new_outcome == RINGER_FAILURE:
            if attending_character:
                raise ValueError("Cannot change to a different character when declaring a ringer outcome")
            self.attending_character = None
        # If it's a character outcome, check to see if this attendance has a character
        elif (new_outcome == DEATH or new_outcome == WIN or new_outcome == LOSS or new_outcome == DECLINED) \
            and not (hasattr(self, "attending_character") and self.attending_character):
            if not attending_character:
                raise ValueError("Must pass character when changing ringer outcome to contractor outcome")
        # If we're changing attending character, do so
        changed_character = False
        if attending_character:
            if not self.attending_character or (self.attending_character.id != attending_character.id):
                changed_character = True
                for journal in self.journal_set.all():
                    journal.void_reward()
            self.attending_character = attending_character
            # Update invited player if necessary
            if hasattr(self, "game_invite") and self.game_invite:
                if self.attending_character.player != self.game_invite.invited_player:
                    self.game_invite.invited_player = self.attending_character.player
                    self.game_invite.save()
        self.outcome = new_outcome
        self.is_confirmed = is_confirmed
        self.is_mvp = is_mvp
        self.save()
        self.give_reward()
        if changed_character:
            for journal in self.journal_set.all():
                journal.grant_reward()

    def give_reward(self):
        if not self.is_confirmed:
            return None
        if self.get_rewards().count() > 0:
            raise ValueError("attendance is granting rewards when it already has one. Attendance: " +
                             str(self.id))
        if self.experience_reward:
            raise ValueError("attendance is granting exp reward when it already has one. Attendance: " +
                             str(self.id))
        if self.mvp_reward:
            raise ValueError("attendance is granting MVP exp reward when it already has one. Attendance: " +
                             str(self.id))
        if self.outcome is None:
            raise ValueError("Error, game attendance has no outcome when game is being transitioned to finished." +
                             str(self.id))
        if self.is_victory():
            player_reward = Reward(relevant_game=self.relevant_game,
                                   rewarded_character=self.attending_character,
                                   rewarded_player=self.attending_character.player,
                                   is_improvement=False)
            player_reward.save()
        elif self.attending_character and self.is_death():
            charon_coin_reward = Reward(relevant_game=self.relevant_game,
                                        rewarded_player=self.attending_character.player,
                                        is_improvement=False,
                                        is_charon_coin=True,)
            charon_coin_reward.save()
        if self.attending_character and not self.is_death() and not self.is_declined_invite():
            if self.relevant_game.id < EXP_V1_V2_GAME_ID:
                reward_type = EXP_WIN_V1 if self.is_victory() else EXP_LOSS_V1
            elif self.attending_character.cell and self.attending_character.cell == self.relevant_game.cell:
                reward_type = EXP_WIN_IN_WORLD_V2 if self.is_victory() else EXP_LOSS_IN_WORLD_V2
            else:
                reward_type = EXP_WIN_V3 if self.is_victory() else EXP_LOSS_V3
            exp_reward = ExperienceReward(
                rewarded_character=self.attending_character,
                rewarded_player=self.attending_character.player,
                type=reward_type,
            )
            exp_reward.save()
            self.experience_reward = exp_reward
            self.save()
        elif self.is_ringer_victory() or self.is_ringer_failure():
            exp_reward = ExperienceReward(
                rewarded_player=self.game_invite.invited_player,
                type=EXP_WIN_RINGER_V2 if self.is_ringer_victory() else EXP_LOSS_RINGER_V2
            )
            exp_reward.save()
            self.experience_reward = exp_reward
            self.save()
        if self.is_mvp and self.relevant_game.id > EXP_V1_V2_GAME_ID:
            exp_reward = ExperienceReward(
                rewarded_character=self.attending_character,
                rewarded_player=self.attending_character.player,
                type=EXP_MVP,
            )
            exp_reward.save()
            self.mvp_reward = exp_reward
            self.save()
            if hasattr(self, "attending_character") and self.attending_character is not None:
                # MVP improvement
                num_mvp_awards = Reward.objects.filter(is_void=False, is_MVP=True, rewarded_character=self.attending_character).count()
                num_mvp_games = Game_Attendance.objects.filter(is_confirmed=True, attending_character=self.attending_character, is_mvp=True).count()
                if num_mvp_games % 3 == 0:
                    if num_mvp_awards >= num_mvp_games // 3:
                        raise ValueError("Character has too many MVP awards. Attendance: " + str(self.pk))
                    mvp_reward = Reward(relevant_game=self.relevant_game,
                                        rewarded_character=self.attending_character,
                                        rewarded_player=self.attending_character.player,
                                        is_improvement=True,
                                        is_MVP=True)
                    mvp_reward.save()



    # Save attendance, creating scenario discoveries as needed, killing characters if needed, and setting GM perms on the
    # character
    def save(self, *args, **kwargs):
        game = self.relevant_game
        if self.get_player() == game.gm:
            raise ValueError("GM cannot attend their own game.")
        if hasattr(self, "attending_character") and self.attending_character and hasattr(self, "game_invite") and self.game_invite:
            if self.attending_character.player != self.game_invite.invited_player:
                raise ValueError("Attendance's invited player and attending_character's player differ!")
        if self.outcome and not (hasattr(self, "attending_character") and self.attending_character):
            if not (self.is_ringer_victory() or self.is_ringer_failure()):
                raise ValueError("Cannot save a non-ringer completed attendance without a character")
        if self.outcome and self.attending_character and self.is_confirmed:
            # if game is finished, reveal scenario to those who brought characters.
            game.scenario.played_discovery(self.attending_character.player)
        if self.pk is not None:
            orig = Game_Attendance.objects.get(pk=self.pk)
            if orig.attending_character and orig.attending_character != self.attending_character:
                #if attending character has changed
                orig.attending_character.default_perms_char_and_powers_to_player(self.relevant_game.gm)
        if self.outcome == OUTCOME[2][0] and not self.character_death and self.is_confirmed and self.attending_character:
            if not self.attending_character.character_death_set.filter(is_void=False).exists():
                self.attending_character.kill()
            char_real_death = self.attending_character.real_death()
            if not hasattr(char_real_death, "game_attendance"):
                self.character_death = self.attending_character.real_death()
        super(Game_Attendance, self).save(*args, **kwargs)
        if (self.relevant_game.is_scheduled() or self.relevant_game.is_active()) and self.attending_character:
            self.attending_character.reveal_char_and_powers_to_player(self.relevant_game.gm)
        elif self.attending_character:
            self.attending_character.default_perms_char_and_powers_to_player(self.relevant_game.gm)
        if (not hasattr(self, "attending_character") or self.attending_character is None) and self.is_confirmed and hasattr(self, "game_invite") and self.game_invite is not None:
            self.relevant_game.scenario.unlocked_discovery(self.game_invite.invited_player)

    # prevent double attendance
    class Meta:
        unique_together = (("attending_character", "relevant_game"))

    def render_timeline_display(self, user, var):
        rewards = self.get_rewards()
        spent_reward = None
        for reward in rewards:
            spent_reward = reward is None or (hasattr(reward, "relevant_power") and reward.relevant_power is not None)
        spent_exp = not hasattr(self, "experience_reward") or (self.experience_reward and self.experience_reward.rewarded_character and self.experience_reward.rewarded_character.unspent_experience() < 3)
        if spent_exp and spent_reward:
            return None
        if self.attending_character:
            reward_url = reverse("characters:characters_spend_reward", args=[self.attending_character.id])
        else:
            reward_url = reverse("characters:characters_allocate_gm_exp")
        context = {
            "url": reward_url,
            "attendance": self
        }
        return render_to_string("games/timeline/timeline_attendance_reward.html", context)

    def render_timeline_header(self, user, var):
        return None


class Game_Invite(models.Model):
    invited_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.PROTECT)
    relevant_game = models.ForeignKey(Game,
                                      on_delete=models.PROTECT)
    is_declined = models.BooleanField(default=False)
    invite_text = models.TextField(max_length=5500,
                                   null=True,
                                   blank=True)
    attendance = models.OneToOneField(Game_Attendance,
                                   blank=True,
                                   null=True,
                                    on_delete=models.CASCADE)
    as_ringer = models.BooleanField(default=False)

    #prevent double invitations.
    class Meta:
        unique_together = (("invited_player", "relevant_game"))

    def __str__(self):
        status = "DECLINED" if self.is_declined else "ACCEPTED" if hasattr(self, "attendance") and self.attendance \
            else "OPEN" if self.relevant_game.is_scheduled() else "EXPIRED"
        return "[{}] {} invitation to {}".format(status, self.invited_player.username, self.relevant_game.scenario.title)

    def get_available_characters(self):
        users_living_character_ids = [char.id for char in
                                      self.invited_player.character_set.filter(is_deleted=False, is_dead=False).all()]
        required_status = self.relevant_game.required_character_status
        if required_status == REQ_STATUS_ANY:
            queryset = Character.objects.filter(id__in=users_living_character_ids)
        elif required_status == REQ_STATUS_NEWBIE_OR_NOVICE:
            queryset = Character.objects.filter(id__in=users_living_character_ids)\
                .filter(status__in=[STATUS_NEWBIE, STATUS_NOVICE])
        elif required_status == REQ_STATUS_NEWBIE:
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(status=STATUS_NEWBIE)
        elif required_status == REQ_STATUS_NOVICE:
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(status=STATUS_NOVICE)
        elif required_status == REQ_STATUS_SEASONED:
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(
                Q(status=STATUS_SEASONED) | Q(ported=SEASONED_PORTED))
        elif required_status == REQ_STATUS_PROFESSIONAL:
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(
                Q(status=STATUS_PROFESSIONAL) | Q(ported=SEASONED_PORTED))
        elif required_status == REQ_STATUS_VETERAN:
            queryset = Character.objects.filter(id__in=users_living_character_ids).filter(
                Q(status=STATUS_VETERAN) | Q(ported=VETERAN_PORTED))
        else:
            raise ValueError("unanticipated required roller status")
        return queryset


    def notify_invitee(self, request, game):
        NotifyGameInvitee.send_robust(sender=self.__class__,
                                      game_invite=self,
                                      request=request)

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(Game_Invite, self).save(*args, **kwargs)
        else:
            super(Game_Invite, self).save(*args, **kwargs)

    def invitee_is_spoiled_on_scenario(self):
        return self.invited_player.has_perm("view_scenario", self.relevant_game.scenario)


class Scenario(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='scenario_creator',
        on_delete=models.PROTECT)
    title = models.CharField(max_length=130)
    summary = models.TextField(max_length=5000, blank=True, null=True)
    description = models.TextField(max_length=74000, blank=True)
    is_wiki_editable = models.BooleanField(default=True)
    wiki_edit_mode = models.CharField(choices=WIKI_EDIT_MODE,
                                        max_length=50,
                                        default=WIKI_EDIT_ALL)
    objective = models.TextField(max_length=5000, blank=True)
    created_date = models.DateTimeField('date created', auto_now_add=True)

    suggested_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=STATUS_ANY)
    exchange_information = models.CharField(max_length=1000, blank=True)

    max_players = models.IntegerField("Suggested Maximum number of players")
    min_players = models.IntegerField("Suggested Minimum number of players")
    cycle = models.ForeignKey("Cycle",
                               blank=True,
                               null=True,
                              on_delete=models.PROTECT)
    order_in_cycle = models.IntegerField(blank=True, null=True)
    is_highlander = models.BooleanField(default=False)
    requires_ringer = models.BooleanField(default=False)
    is_rivalry = models.BooleanField(default=False)
    available_to = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                         through="Scenario_Discovery",
                                         through_fields=('relevant_scenario', 'discovering_player'),
                                         default=None,
                                         blank=True)
    stock_elements = models.ManyToManyField(StockWorldElement,
                                          through="ScenarioElement",
                                          through_fields=('relevant_scenario', 'relevant_element'),
                                          default=None,
                                          blank=True)
    tags = models.ManyToManyField("ScenarioTag", blank=True)

    num_words = models.IntegerField("Number of Words", default=0)
    times_run = models.IntegerField("Number of times Scenario has been run", default=0)
    num_gms_run = models.IntegerField("Number of GMs who have run Scenario", default=0)
    num_victories = models.IntegerField("Number of victories awarded in this Scenario", default=0)
    num_deaths = models.IntegerField("Number of deaths caused by this Scenario", default=0)
    deadliness_ratio = models.FloatField("A denormalization of deaths over victories", default=0)
    num_times_purchased = models.IntegerField("Number of times this Scenario was purchased on the exchange", default=0)
    exclude_from_leaderboard = models.BooleanField(default=False)

    is_on_exchange = models.BooleanField(default=False)
    date_added_to_exchange = models.DateTimeField(blank=True, null=True)


    class Meta:
        permissions = (
            ('edit_scenario', 'Edit scenario'),
        )
        indexes = [
            models.Index(fields=['times_run']),
            models.Index(fields=['num_gms_run']),
            models.Index(fields=['num_victories']),
            models.Index(fields=['num_deaths']),
            models.Index(fields=['deadliness_ratio']),
            models.Index(fields=['creator']),
        ]

    def __str__(self):
        return self.title

    def is_developer_written(self):
        return self.creator_id in [169, 23, 272, 1]


    def can_submit_to_exchange(self):
        if self.is_on_exchange:
            return False
        latest_approval = ScenarioApproval.objects.filter(relevant_scenario=self).order_by("-created_date").first()
        if latest_approval is not None and latest_approval.is_waiting():
            return False
        return len(self.get_steps_to_receive_improvement()) == 0

    def get_scheduled_or_active_game_for_gm(self, gm):
        return Game.objects.filter(scenario=self, gm=gm)\
            .exclude(get_scheduled_game_excludes_query())\
            .prefetch_related("attended_by").all()

    def get_active_characters_for_gm(self, gm):
        games = self.get_scheduled_or_active_game_for_gm(gm)
        if games:
            characters = reduce(lambda a, b: a.union(b), [x.attended_by.all() for x in games])
            return characters
        else:
            return Character.objects.none()

    def num_times_purchased_since_last_submission(self):
        latest_approval = ScenarioApproval.objects\
            .filter(relevant_scenario=self, status=APPROVED).order_by("-created_date").first()
        if latest_approval:
            return Scenario_Discovery.objects\
                .filter(relevant_scenario=self, created_date__gt=latest_approval.created_date, reason=DISCOVERY_PURCHASED)\
                .count()
        else:
            return 0

    def remove_from_exchange(self):
        if not self.is_on_exchange:
            return
        if self.num_times_purchased_since_last_submission() < 4:
            latest_approval = ScenarioApproval.objects \
                .filter(relevant_scenario=self, status=APPROVED).order_by("-created_date").first()
            if latest_approval and hasattr(latest_approval, "experience_reward") and latest_approval.experience_reward:
                latest_approval.experience_reward.mark_void()
            profile = self.creator.profile
            ExchangeCreditChange.objects.create(rewarded_player=profile.user,
                                                reason="Removed {} from the Exchange".format(self.title),
                                                value=-EXCHANGE_SUBMISSION_VALUE)
            profile.exchange_credits = profile.exchange_credits - EXCHANGE_SUBMISSION_VALUE
            profile.save()
        ScenarioApproval.objects.create(relevant_scenario=self, status=REMOVED)
        self.is_on_exchange = False
        self.save()

    def player_has_gmed(self, gm):
        return Game.objects.filter(scenario=self, gm=gm).exists()

    def get_completed_games_for_gm(self, gm):
        return Game.objects.filter(scenario=self, gm=gm) \
            .exclude(get_completed_game_excludes_query()) \
            .prefetch_related("attended_by").all()

    def get_finished_characters_for_gm(self, gm):
        games = self.get_completed_games_for_gm(gm)
        if games:
            characters = reduce(lambda a, b: a.union(b), [x.attended_by.all() for x in games])
            return characters
        else:
            return Character.objects.none()

    def get_players_gmed_for(self, gm):
        games = self.get_completed_games_for_gm(gm)
        if games:
            players = reduce(lambda a, b: a.union(b), [x.invitations.all() for x in games])
            return players
        else:
            return get_user_model().objects.none()

    def player_can_edit_writeup(self, user):
        if user == self.creator or user.is_superuser:
            return True
        if self.is_wiki_editable and self.player_is_spoiled(user):
            if self.wiki_edit_mode == WIKI_EDIT_ALL:
                return True
            if self.wiki_edit_mode == WIKI_EDIT_EXCHANGE and user.profile.exchange_contributor:
                return True
        return False

    def is_valid(self):
        return self.num_words > 1000

    def get_steps_to_receive_improvement(self):
        reasons = []
        if not self.is_valid():
            reasons.append("Minimum 1000 words. ")
        if self.num_finished_games() == 0:
            reasons.append("Must be run as a Contract. ")
        return reasons

    def get_active_improvement(self):
        return get_object_or_none(Reward,
                                  rewarded_player=self.creator,
                                  relevant_scenario=self,
                                  is_void=False)

    def _grant_reward(self):
        reward = Reward(relevant_scenario=self,
                        rewarded_player=self.creator,
                        is_improvement=True)
        reward.save()
        Notification.objects.create(
            user=self.creator,
            headline="You've earned an Improvement",
            content="From writing up {}".format(self.title),
            url=reverse("games:games_allocate_improvement_generic"),
            notif_type=REWARD_NOTIF)

    def grant_or_void_reward_as_necessary(self):
        improvement_steps = self.get_steps_to_receive_improvement()
        active_improvement = self.get_active_improvement()
        if len(improvement_steps) == 0:
            # should have improvement
            if not active_improvement:
                self._grant_reward()
        else:
            # shouldn't have improvement
            if active_improvement:
                active_improvement.mark_void()

    def last_run_time(self):
        last_run = self.game_set.exclude(get_completed_game_excludes_query()).order_by("-end_time").first()
        if last_run is not None:
            return last_run.end_time
        else:
            return None


    def update_stats(self):
        self.times_run = self.game_set.exclude(get_completed_game_excludes_query()).count()
        self.num_gms_run = Game.objects \
            .filter(scenario=self) \
            .exclude(get_completed_game_excludes_query()) \
            .aggregate(Count('gm_id', distinct=True))['gm_id__count']
        self.num_victories = Game_Attendance.objects.filter(relevant_game__scenario=self, outcome=WIN, is_confirmed=True).count()
        self.num_deaths = Game_Attendance.objects.filter(relevant_game__scenario=self, outcome=DEATH, is_confirmed=True).count()
        self.deadliness_ratio = self.num_deaths / max(self.num_victories, 1)
        self.save()

    def is_public(self):
        public = self.tags.filter(slug="public").exists()
        return public

    def player_is_spoiled(self, player):
        return player.has_perm("view_scenario", self)

    def is_player_aftermath_spoiled(self, player):
        if player.is_anonymous:
            return False
        if player.has_perm("view_scenario", self):
            return Scenario_Discovery.objects.filter(relevant_scenario=self, discovering_player=player, is_aftermath_spoiled=True).exists()
        return False

    def is_spoilable_for_player(self, player):
        if player.is_anonymous:
            return False
        return Scenario_Discovery.objects.filter(relevant_scenario=self, discovering_player=player, is_spoiled=False).exists()

    def player_discovered(self, player):
        if player.is_anonymous:
            return False
        return Scenario_Discovery.objects.filter(relevant_scenario=self, discovering_player=player).exists()

    def spoil_aftermath(self, player):
        Scenario_Discovery.objects.filter(relevant_scenario=self, discovering_player=player).first().spoil_aftermath()

    def spoil_already_discovered(self, player):
        Scenario_Discovery.objects.filter(relevant_scenario=self, discovering_player=player).get().spoil()

    def discovery_for_player(self, player):
        return get_object_or_none(Scenario_Discovery, relevant_scenario=self, discovering_player=player)

    def choice_txt(self):
        return "{} ({} words, {}-{} {} Contractors)".format(self.title, self.num_words, self.min_players, self.max_players, self.get_suggested_status_display())

    def finished_games(self):
        return self.game_set.exclude(get_completed_game_excludes_query())

    def num_finished_games(self):
        return self.finished_games().count()

    def played_discovery(self, player):
        discovery = Scenario_Discovery.objects.filter(relevant_scenario=self.id, discovering_player=player).first()
        if discovery is None:
            discovery = Scenario_Discovery (
                discovering_player=player,
                relevant_scenario=self,
                reason=DISCOVERY_REASON[0][0],
                is_spoiled=True,
                is_aftermath_spoiled=False,
            )
            discovery.save()
        else:
            discovery.is_spoiled = True
            discovery.save()

    def unlocked_discovery(self, player, notify=True):
        if not player.scenario_set.filter(id=self.id).exists():
            discovery = Scenario_Discovery(
                discovering_player=player,
                relevant_scenario=self,
                reason=DISCOVERY_REASON[3][0],
                is_spoiled=False,
            )
            discovery.save()
            if notify:
                Notification.objects.create(
                    user=player,
                    headline="You've unlocked a Scenario",
                    content="{}".format(self.title),
                    url=reverse("games:games_view_scenario", args=(self.pk,)),
                    notif_type=SCENARIO_NOTIF,
                    is_timeline=True,
                    article=discovery)
            return discovery
        return None

    def share(self, with_player, sharing_player, notify=True):
        if not with_player.scenario_set.filter(id=self.id).exists():
            discovery = Scenario_Discovery(
                discovering_player=with_player,
                relevant_scenario=self,
                reason=DISCOVERY_REASON[2][0],
                is_spoiled=False,
            )
            discovery.save()
            if notify:
                Notification.objects.create(
                    user=with_player,
                    headline="{} shared a Scenario".format(sharing_player.username),
                    content="{}".format(self.title),
                    url=reverse("games:games_view_scenario", args=(self.pk,)),
                    notif_type=SCENARIO_NOTIF,
                    is_timeline=True,
                    article=discovery)
            return discovery
        return None

    def purchase(self, player):
        if not player.scenario_set.filter(id=self.id).exists():
            if player.profile.exchange_credits < EXCHANGE_SCENARIO_COST:
                return ValueError("Insufficient funds")
            discovery = Scenario_Discovery(
                discovering_player=player,
                relevant_scenario=self,
                reason=DISCOVERY_PURCHASED,
                is_spoiled=False,
            )
            discovery.save()
            ExchangeCreditChange.objects.create(rewarded_player=player,
                                                reason="Purchased {} on the Exchange".format(self.title),
                                                value=-EXCHANGE_SCENARIO_COST)
            player.profile.exchange_credits = player.profile.exchange_credits - EXCHANGE_SCENARIO_COST
            player.profile.save()
            Notification.objects.create(
                user=player,
                headline="You've purchased a Scenario",
                content="{}".format(self.title),
                url=reverse("games:games_view_scenario", args=(self.pk,)),
                notif_type=SCENARIO_NOTIF,
                is_timeline=True,
                article=discovery)
            self.num_times_purchased = self.num_times_purchased + 1
            self.save()
            return discovery
        return None

    def is_stock(self):
        return self.tags.count() > 0

    def update_word_count(self):
        total_words = 0
        all_sections = self.get_latest_of_all_writeup_sections()
        for section in all_sections:
            total_words += section.num_words
        self.num_words = total_words

    def get_latest_of_section(self, section):
        return ScenarioWriteup.objects\
            .filter(relevant_scenario=self, section=section, is_deleted=False)\
            .order_by("-created_date")\
            .first()

    def get_latest_of_all_writeup_sections(self):
        sections = []
        for section_type in WRITEUP_SECTION:
            section = self.get_latest_of_section(section_type[0])
            if section and section.content:
                sections.append(section)
        return sections

    def get_latest_of_all_elements(self):
        return self.scenarioelement_set \
            .order_by().order_by("designation", "-created_date") \
            .distinct("designation") \
            .select_related("relevant_element")

    def get_latest_of_all_elements_of_type(self, element_type):
        return self.scenarioelement_set.filter(type=element_type)\
            .order_by().order_by("designation", "-created_date")\
            .distinct("designation")\
            .select_related("relevant_element")

    def get_last_edit(self):
        return ScenarioWriteup.objects \
            .filter(relevant_scenario=self, is_deleted=False) \
            .order_by("-created_date") \
            .first()

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(Scenario, self).save(*args, **kwargs)
            discovery = Scenario_Discovery (
                discovering_player = self.creator,
                relevant_scenario = self,
                reason = DISCOVERY_REASON[1][0],
                is_spoiled=True
            )
            discovery.save()
        else:
            super(Scenario, self).save(*args, **kwargs)
        self.grant_or_void_reward_as_necessary()


class ScenarioWriteup(models.Model):
    writer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='scenario_writer',
        on_delete=models.PROTECT)
    section = models.CharField(choices=WRITEUP_SECTION,
                               max_length=55,
                               default=MISSION)
    content = models.TextField(max_length=99000)
    relevant_scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    num_words = models.IntegerField("Number of Words", default=0)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_scenario', 'section', 'is_deleted', 'created_date']),
            models.Index(fields=['relevant_scenario', 'section', 'created_date']),
            models.Index(fields=['relevant_scenario', 'created_date']),
            models.Index(fields=['writer']),
        ]

    def __str__(self):
        return "[{}] (by {}) {}".format(
            self.get_section_display(),
            self.writer.username,
            self.relevant_scenario.title,)

    def save(self, *args, **kwargs):
        self.__update_word_count()
        super(ScenarioWriteup, self).save(*args, **kwargs)

    def scenario_writer(self):
        return self.relevant_scenario.creator

    def is_community_edit(self):
        return self.relevant_scenario.creator != self.writer

    def to_blob(self, request, aftermath_spoiled):
        blob = model_to_dict(self)
        blob["created_date"] = self.created_date
        blob["section_display"] = self.get_section_display()
        blob["writer_url"] = request.build_absolute_uri(reverse('profiles:profiles_view_profile', args=(self.writer.id,)))
        blob["writer_username"] = self.writer.username
        blob["is_element"] = False
        if not aftermath_spoiled and self.is_aftermath():
            spoil_aftermath_url = request.build_absolute_uri(reverse('games:spoil_scenario_aftermath', args=(self.relevant_scenario.id, "view")))
            spoil_aftermath_link = '<a href="{}">Click Here</a> to spoil the aftermath'.format(spoil_aftermath_url)
            content = "<i>Section hidden because you have not yet spoiled this Scenario's aftermath. {}</i>".format(spoil_aftermath_link)
            blob["content"] = content
        return blob


    def get_section_subheader(self):
        if self.section == OVERVIEW:
            return ""
        if self.section == BACKSTORY:
            return "GM Pre-reading. Understand the situation."
        if self.section == INTRODUCTION:
            return "Try to finish introductions within the first hour of the session. " \
                   "Read more about GMing introductions " \
                   "<a href=\"https://thecontractrpg.com/guide/gm-manual/#contractor-introductions\" target=\"_blank\" rel=\"noopener noreferrer\">here.</a>"
        return ""

    def is_most_recent_for_section(self):
        most_recent = ScenarioWriteup.objects.filter(relevant_scenario=self.relevant_scenario, section=self.section).order_by("-created_date").first()
        return most_recent == self

    def should_display_objective(self):
        return self.section in [INTRODUCTION, MISSION, AFTERMATH]

    def is_overview(self):
        return self.section in [OVERVIEW]

    def is_aftermath(self):
        return self.section == AFTERMATH

    def __update_word_count(self):
        soup = BeautifulSoup(self.content, features="html.parser")
        self.num_words = len(soup.text.split())


class ScenarioElement(models.Model):
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    designation = models.CharField(max_length=130) # e.g. "Condition 1"
    relevant_element = models.ForeignKey(StockWorldElement, on_delete=models.CASCADE)
    relevant_scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    type = models.CharField(choices=ELEMENT_TYPE, max_length=45, default=CONDITION)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ("relevant_element", "relevant_scenario")
        indexes = [
            models.Index(fields=['relevant_scenario', 'designation', 'created_date']),
            models.Index(fields=['relevant_scenario', 'created_date']),
        ]

    def get_type_plural(self):
        if self.type == LOOSE_END:
            return "Loose Ends"
        if self.type == CONDITION:
            return "Conditions"
        if self.type == CIRCUMSTANCE:
            return "Circumstances"
        if self.type == TROPHY:
            return "Trophies"

    def to_blob(self, request, aftermath_spoiled):
        blob = model_to_dict(self)
        blob["created_date"] = self.created_date
        blob["section_display"] = "{}: {}".format(self.designation, self.relevant_element.name)
        blob["section"] = self.designation
        blob["writer_url"] = request.build_absolute_uri(reverse('profiles:profiles_view_profile', args=(self.creator.id,)))
        blob["writer_username"] = self.creator.username
        blob["num_words"] = self.relevant_element.count_words()
        if aftermath_spoiled:
            blob["content"] = render_scenario_element(self, request)
        else:
            spoil_aftermath_url = request.build_absolute_uri(reverse('games:spoil_scenario_aftermath', args=(self.relevant_scenario.id, "view")))
            spoil_aftermath_link = '<a href="{}">Click Here</a> to spoil the aftermath'.format(spoil_aftermath_url)
            content = "<i>Handout hidden because you have not yet spoiled this Scenario's aftermath. {}</i>".format(spoil_aftermath_link)
            blob["content"] = content
        blob["is_element"] = True
        return blob


class Scenario_Discovery(models.Model):
    discovering_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                           on_delete=models.CASCADE)
    relevant_scenario = models.ForeignKey(Scenario,
                                          on_delete=models.CASCADE)
    reason = models.CharField(choices=DISCOVERY_REASON,
                              max_length=25)
    sharing_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.CASCADE,
                                       null=True,
                                       related_name="scenario_shares")
    is_spoiled = models.BooleanField(default=True)
    is_aftermath_spoiled = models.BooleanField(default=True)
    created_date = models.DateTimeField('date created', auto_now_add=True, null=True, blank=True)

    # prevent double discoveries.
    class Meta:
        unique_together = (("discovering_player", "relevant_scenario"))

    def __str__(self):
        return "{} {} {}".format(self.discovering_player.username, self.get_reason_display(), self.relevant_scenario)

    def spoil(self):
        self.is_spoiled = True
        self.is_aftermath_spoiled = True
        self.save()
        assign_perm('view_scenario', self.discovering_player, self.relevant_scenario)

    def spoil_aftermath(self):
        if self.is_spoiled:
            self.is_aftermath_spoiled = True
            self.save()
        else:
            raise ValueError("Need to spoil scenario to spoil aftermath")

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(Scenario_Discovery, self).save(*args, **kwargs)
            if self.is_spoiled:
                assign_perm('view_scenario', self.discovering_player, self.relevant_scenario)
            if self.reason == DISCOVERY_REASON[1][0]: # created
                assign_perm('edit_scenario', self.discovering_player, self.relevant_scenario)
        else:
            super(Scenario_Discovery, self).save(*args, **kwargs)

    def render_timeline_display(self, user, var):
        context = {
            "url": reverse("games:games_view_scenario", args=(self.relevant_scenario_id,)),
            "discovery": self
        }
        return render_to_string("games/timeline/timeline_scenario_discovery.html", context)

    def render_timeline_header(self, user, var):
        return None


class Cycle(models.Model):
    # A cycle represents a set of scenarios that have a throughline in the plot
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE)
    title = models.CharField(max_length=130)
    summary = models.TextField(max_length=5000)


class Reward(models.Model):
    relevant_game = models.ForeignKey(
        Game,
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    relevant_scenario = models.ForeignKey(
        Scenario,
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    relevant_power = models.ForeignKey(
        Power,
        null=True,
        blank=True,
        related_name='relevant_power',
        on_delete=models.CASCADE)
    source_asset = models.ForeignKey(
        AssetDetails,
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    rewarded_character = models.ForeignKey(
        Character,
        null=True,
        blank=True,
        on_delete=models.CASCADE)
    rewarded_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='rewarded_player',
        on_delete=models.CASCADE)
    is_improvement = models.BooleanField(default=True)
    is_gm_reward = models.BooleanField(default=False)
    is_ported_reward = models.BooleanField(default=False)
    is_charon_coin = models.BooleanField(default=False)
    is_void = models.BooleanField(default=False)
    is_journal = models.BooleanField(default=False)
    is_new_player_gm_reward = models.BooleanField(default=False)
    is_questionnaire = models.BooleanField(default=False)
    is_MVP = models.BooleanField(default=False)

    awarded_on = models.DateTimeField('awarded on')
    assigned_on = models.DateTimeField('assigned on',
                                            null=True,
                                            blank=True)

    def __str__(self):
        return "{} {} ({})".format(self.type_text(),
                                   self.rewarded_player.username,
                                   self.rewarded_character.name if self.rewarded_character else "unassigned")


    def grant_to_character(self, character):
        if not character:
            raise ValueError("must provide character when assigning reward!")
        if self.rewarded_character:
            # instead may want to refund and then assign new reward?
            raise ValueError("reward already assigned!")
        if not self.is_charon_coin:
            #TODO: use this method to grant improvements as well.
            raise ValueError("model granting non-charon rewards not implemented yet")
        self.rewarded_character = character
        self.save()


    def save(self, *args, **kwargs):
        if not self.is_void:
            if self.relevant_power and self.relevant_power.parent_power.character.id != self.rewarded_character.id:
                raise ValueError("ERROR: cannot assign gifts to other players' characters")
            if self.rewarded_character is None and (not self.is_improvement and not self.is_charon_coin):
                raise ValueError("ERROR: invalid unassigned reward")
            if self.is_charon_coin:
                if self.rewarded_character and self.rewarded_character.assigned_coin() and self.rewarded_character.assigned_coin().id != self.id:
                    raise ValueError("ERROR: cannot assign more than one coin to a character")

        if self.pk is None:
            if self.awarded_on is None:
                self.awarded_on = timezone.now()
        super(Reward, self).save(*args, **kwargs)

    def refund_keeping_character_assignment(self):
        self.mark_void()
        # create new reward by setting pk to none and saving
        self.pk = None
        self.is_void = False
        self.relevant_power = None
        self.save()

    def refund_and_unassign_from_character(self):
        character = None if self.is_charon_coin or self.is_new_player_gm_reward or self.is_improvement else self.rewarded_character
        self.mark_void()
        # create new reward by setting pk to none and saving
        self.pk = None
        self.is_void = False
        self.relevant_power = None
        self.rewarded_character = character
        self.save()

    def mark_void(self):
        self.is_void = True
        self.save()

    def assign_to_power(self, power):
        self.relevant_power = power
        if not self.rewarded_character:
            if power.parent_power.owner:
                self.rewarded_character = power.parent_power.owner
            else:
                print("cannot assign reward to Gift without owner. reward, power " + str(self.id)+ " " + str(power.id))
                return
        self.assigned_on = timezone.now()
        self.save()

    def active(self):
        return not self.is_void

    def type_text(self):
        if self.is_improvement:
            return "Improvement"
        else:
            return "Gift"

    def reason_text(self):
        if self.relevant_game:
            if self.relevant_game.gm_id == self.rewarded_player_id:
                if self.is_new_player_gm_reward:
                    reason = "running for a new Player: "
                elif self.is_gm_reward:
                    reason = "running "
                else:
                    reason = "achieving the Golden Ratio running "
            elif self.is_charon_coin:
                reason = "dying in "
            elif self.is_journal:
                reason = "writing a Journal for "
            elif self.is_questionnaire:
                return "answering questions for their questionnaire"
            elif self.is_MVP:
                reason = "Earning commission in "
            else:
                reason = "playing in "
            reason = reason + self.relevant_game.scenario.title
            return reason
        if self.relevant_scenario:
            return "writing up " + self.relevant_scenario.title
        if self.source_asset:
            return "the Asset " + self.source_asset.relevant_asset.name
        if self.is_charon_coin:
            return "losing a Contractor in a Side Game"
        if self.is_ported_reward:
            return "House Games of yore"


class ScenarioTag(models.Model):
    tag = models.CharField(max_length=40)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=40,
                            primary_key=True)
    unlock_instructions = models.CharField(max_length=400, default=".")

    def __str__(self):
        return self.tag


class GameMedium(models.Model):
    medium = models.CharField(max_length=40)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=40,
                            primary_key=True)
    color = models.CharField("Css Color",
                             max_length=40)

    def __str__(self):
        return self.medium


class Move(models.Model):
    main_character = models.ForeignKey(Character, on_delete=models.PROTECT)
    gm = models.ForeignKey( settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    # Cannot make a move before first Downtime. HOWEVER, if an attendance is changed, this downtime can become blank
    downtime = models.ForeignKey(Game_Attendance,
                                 blank=True,
                                 null=True,
                                 on_delete=models.CASCADE)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE)
    title = models.TextField(max_length=500, blank=True)
    summary = models.TextField(max_length=50000, blank=True)

    # Rewards and public event
    public_event = models.OneToOneField(WorldEvent, on_delete=models.CASCADE)
    gm_experience_reward = models.OneToOneField(ExperienceReward, null=True, blank=True, on_delete=models.CASCADE)
    is_valid = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)

    deleted_on = models.DateTimeField('date deleted', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['main_character', 'created_date']), # display on sheet
            models.Index(fields=['main_character', 'downtime']), # display on journal
            models.Index(fields=['gm', 'created_date']), # display on gm profile
            models.Index(fields=['cell', 'created_date']), # display in cell / world events
            models.Index(fields=['gm_experience_reward']), # exp progeny
        ]

    def __repr__(self):
        return "[{} in {}] {}".format(self.main_character.name, self.cell.name, self.title)

    def __str__(self):
        return self.__repr__()

    def save(self, *args, **kwargs):
        self.__update_is_valid()
        super(Move, self).save(*args, **kwargs)
        self.fix_rewards()

    def fix_rewards(self):
        self.__update_is_valid()
        if self.is_valid and (not self.gm_experience_reward or self.gm_experience_reward.is_void):
            self.__grant_gm_exp_reward()
        if (not self.is_valid) and (self.gm_experience_reward and not self.gm_experience_reward.is_void):
            self.refund_reward()

    def mark_void(self):
        if self.deleted_on:
            raise ValueError("Move is already void")
        self.deleted_on = timezone.now()
        self.refund_reward()

    def player_can_edit(self, player):
        if player.is_superuser:
            return True
        return player.is_authenticated and (player == self.gm) or self.cell.player_can_manage_games(player)

    def __grant_gm_exp_reward(self):
        if self.gm_experience_reward and not self.gm_experience_reward.is_void:
            raise ValueError("Move is granting exp reward to gm when it already has one.", str(self.id))
        exp_reward = ExperienceReward(
            rewarded_player=self.gm,
            type=EXP_GM_MOVE_V2
        )
        exp_reward.save()
        self.gm_experience_reward = exp_reward
        self.save()

    def refund_reward(self):
        if self.gm_experience_reward and not self.gm_experience_reward.is_void:
            self.gm_experience_reward.mark_void()
            self.experience_reward = None
        self.save()

    def __update_is_valid(self):
        event_words = self.__get_event_wordcount()
        self.is_valid = (event_words > 100) and (event_words + self.__get_summary_wordcount() > 250)

    def __get_event_wordcount(self):
        if hasattr(self, "public_event") and self.public_event and self.public_event.event_description:
            soup = BeautifulSoup(self.public_event.event_description, features="html.parser")
            return len(soup.text.split())
        else:
            return 0

    def __get_summary_wordcount(self):
        return len(self.summary.split())


class ScenarioApproval(models.Model):
    relevant_scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    status = models.CharField(choices=APPROVAL_STATUS, max_length=1000, default=WAITING)
    feedback = models.CharField(max_length=8000, blank=True)
    created_date = models.DateTimeField('date created', auto_now_add=True)
    closed_date = models.DateTimeField(blank=True, null=True)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    experience_reward = models.OneToOneField(ExperienceReward, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return "{} - {}".format(self.relevant_scenario.title, self.get_status_display())

    def is_waiting(self):
        return self.status == WAITING

    def is_removed(self):
        return self.status == REMOVED

    def approve(self, approver):
        self.status = APPROVED
        self.closed_date = timezone.now()
        self.approver = approver
        self.save()

        self.relevant_scenario.is_on_exchange = True
        self.relevant_scenario.date_added_to_exchange = timezone.now()
        if self.relevant_scenario.wiki_edit_mode == WIKI_EDIT_ALL:
            self.relevant_scenario.wiki_edit_mode = WIKI_EDIT_EXCHANGE
        self.relevant_scenario.save()

        # reward scenario writer
        rewarded_approval_count = ScenarioApproval.objects\
            .filter(relevant_scenario=self.relevant_scenario, status=APPROVED, experience_reward__isnull=False,  experience_reward__is_void=False).count()
        if rewarded_approval_count == 0:
            profile = self.relevant_scenario.creator.profile
            ExchangeCreditChange.objects.create(rewarded_player=profile.user,
                                                reason="Donated {} to the Exchange".format(self.relevant_scenario.title),
                                                value=EXCHANGE_SUBMISSION_VALUE)
            profile.exchange_credits = profile.exchange_credits + EXCHANGE_SUBMISSION_VALUE
            reward = ExperienceReward.objects.create(
                rewarded_player=self.relevant_scenario.creator,
                type=EXP_EXCHANGE,
            )
            self.experience_reward = reward
            self.save()

        # Notify
        Notification.objects.create(
            user=self.relevant_scenario.creator,
            headline="Your Scenario has been approved!",
            content="{} is on the Community Scenario Exchange.".format(self.relevant_scenario.title),
            #TODO: change this to the scenario exchange.
            url=reverse('games:games_view_scenario', args=(self.relevant_scenario_id,)),
            notif_type=SCENARIO_NOTIF)

        # Set profile flag for scenario writer
        profile.exchange_contributor = True
        profile.save()

class ExchangeCreditChange(models.Model):
    created_time = models.DateTimeField(auto_now_add=True)
    rewarded_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                        on_delete=models.CASCADE)
    reason = models.CharField(max_length=1000)
    value = models.IntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['rewarded_player', 'created_time']),  # display on timeline
        ]

    def __str__(self):
        return "{} ::: {}".format(self.rewarded_player.username, self.get_display_sentence())

    def get_display_sentence(self):
        verb = "Earned" if self.value > 0 else "Spent"
        amount = abs(self.value)
        return "{} {} Exchange Credits: {}".format(verb, amount, self.reason)