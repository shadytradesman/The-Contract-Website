from django.db import models
from django.conf import settings
from characters.models import Character, HIGH_ROLLER_STATUS, Character_Death, ExperienceReward, AssetDetails
from powers.models import Power
from cells.models import Cell
from django.utils import timezone
from guardian.shortcuts import assign_perm
from postman.api import pm_write
from django.urls import reverse
from django.utils.safestring import SafeText
from games.games_constants import GAME_STATUS

from hgapp.utilities import get_object_or_none

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

DISCOVERY_REASON = (
    ('PLAYED', 'Played'),
    ('CREATED', 'Created'),
    ('SHARED', 'Shared'),
    ('UNLOCKED', 'Unlocked'),
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
    required_character_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=HIGH_ROLLER_STATUS[0][0])
    title = models.CharField(max_length=130)
    hook = models.TextField(max_length=5000,
                            null=True,
                            blank=True)
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
    open_invitations = models.BooleanField(default=True)
    cell = models.ForeignKey(Cell,
                             null=True, # for migration reasons. All games should have cells.
                             blank=True, # for migration reasons. All games should have cells.
                             on_delete=models.CASCADE)
    gm_experience_reward = models.OneToOneField(ExperienceReward,
                                          null=True,
                                          blank=True,
                                          on_delete=models.CASCADE)

    class Meta:
        permissions = (
            ('edit_game', 'Edit game'),
        )

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

    def transition_to_active(self, lock_characters):
        assert(self.is_scheduled())
        if lock_characters:
            for character in self.attended_by.all():
                character.lock_edits()
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
            character.default_perms_char_and_powers_to_player(self.gm)
        self.status = GAME_STATUS[2][0]
        self.end_time = timezone.now()
        self.save()
        self.give_rewards()

    def give_rewards(self):
        if not self.is_finished() and not self.is_recorded():
            print("Game is not finished: " + str(self.id))
            return
        for game_attendance in self.game_attendance_set.all():
            game_attendance.give_reward()
        if self.achieves_golden_ratio():
            gm_reward = Reward(relevant_game=self,
                               rewarded_player=self.gm,
                               is_improvement=True)
            gm_reward.save()
        self._grant_gm_exp_reward()

    def _grant_gm_exp_reward(self):
        exp_reward = ExperienceReward(
            rewarded_player=self.gm,
        )
        exp_reward.save()
        self.gm_experience_reward = exp_reward
        self.save()

    # Determines if the game's golden ratio status has changed and handles GM rewards accordingly.
    def recalculate_golden_ratio(self, original_value):
        current_value = self.achieves_golden_ratio()
        if current_value != original_value:
            if current_value == True:
                gm_reward = Reward(relevant_game=self,
                                   rewarded_player=self.gm,
                                   is_improvement=True)
                gm_reward.save()
                if hasattr(self, "gm_experience_reward") and self.gm_experience_reward:
                    self.gm_experience_reward.mark_void()
                self._grant_gm_exp_reward()
            else:
                self.get_gm_reward().mark_void()

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
        return self.invitations.filter(game_invite__is_declined=False).all()

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
        return self.gm == player or self.game_invite_set.filter(is_declined=False, invited_player=player)

    def update_participant_titles(self):
        self.gm.profile.recompute_titles()
        for invite in self.invitations.all():
            invite.profile.recompute_titles()

    def save(self, *args, **kwargs):
        if not hasattr(self, 'gm'):
            self.gm = self.creator
        if not hasattr(self, 'scenario'):
            scenario = Scenario(creator=self.gm,
                                title=str(self.title),
                                description="Put details of the scenario here",
                                suggested_status=HIGH_ROLLER_STATUS[0][0],
                                max_players=5,
                                min_players=2)
            scenario.save()
            self.scenario = scenario
        if self.pk is None:
            super(Game, self).save(*args, **kwargs)
            assign_perm('view_game', self.creator, self)
            assign_perm('view_game', self.gm, self)
            assign_perm('edit_game', self.creator, self)
        else:
            super(Game, self).save(*args, **kwargs)
        if self.is_recorded() or self.is_archived():
            self.update_participant_titles()

    def __str__(self):
        return "[" + self.status + "] " + self.scenario.title + " run by: " + self.gm.username


class Game_Attendance(models.Model):
    #set to null when ringer.
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
        self.is_confirmed=True
        self.save()
        self.give_reward()

    def get_reward(self):
        return get_object_or_none(Reward, rewarded_player=self.get_player(), relevant_game=self.relevant_game, is_void=False, is_journal=False)

    def get_player(self):
        if self.attending_character:
            return self.attending_character.player
        else:
            return self.game_invite.invited_player

    # Changes the outcome of the GameAttendance. Handles Gifts, Experience Rewards, attending Character, Character death
    # status, and confirmation status. This method does NOT update the Game's golden ratio rewards.
    def change_outcome(self, new_outcome, is_confirmed, attending_character=None):
        current_outcome = self.outcome
        if current_outcome == new_outcome and attending_character == self.attending_character and self.is_confirmed == is_confirmed:
            return
        current_reward = self.get_reward()
        # Void rewards
        if current_reward:
            current_reward.mark_void()
        # Void experience rewards
        if hasattr(self, "experience_reward") and self.experience_reward:
            self.experience_reward.mark_void()
            self.experience_reward = None
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
            if self.attending_character.id != attending_character.id:
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
        self.save()
        self.give_reward()
        if changed_character:
            for journal in self.journal_set.all():
                journal.grant_reward()

    def give_reward(self):
        if not self.is_confirmed or self.get_reward():
            return None
        if self.outcome is None:
            raise ValueError("Error, game attendance has no outcome when game is being transitioned to finished.",
                             str(self.id))
        if self.is_victory():
            player_reward = Reward(relevant_game=self.relevant_game,
                                   rewarded_character=self.attending_character,
                                   rewarded_player=self.attending_character.player,
                                   is_improvement=False)
            player_reward.save()
        if self.attending_character and not self.is_death() and not self.is_declined_invite():
            exp_reward = ExperienceReward(
                rewarded_character=self.attending_character,
                rewarded_player=self.attending_character.player,
            )
            exp_reward.save()
            self.experience_reward = exp_reward
            self.save()
        if self.attending_character and self.is_death():
            charon_coin_reward = Reward(relevant_game=self.relevant_game,
                                   rewarded_player=self.attending_character.player,
                                   is_improvement=False,
                                   is_charon_coin=True,)
            charon_coin_reward.save()
        if self.is_ringer_victory():
            ringer_reward = Reward(relevant_game=self.relevant_game,
                                   rewarded_player=self.game_invite.invited_player,
                                   is_improvement=True)
            ringer_reward.save()
            exp_reward = ExperienceReward(
                rewarded_player=self.game_invite.invited_player,
            )
            exp_reward.save()
            self.experience_reward = exp_reward
            self.save()

    # Save attendance, creating scenario discoveries as needed, killing characters if needed, and setting GM perms on the
    # character
    def save(self, *args, **kwargs):
        game = self.relevant_game
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
            if not self.attending_character.is_dead():
                self.attending_character.kill()
            char_real_death = self.attending_character.real_death()
            if not hasattr(char_real_death, "game_attendance"):
                self.character_death = self.attending_character.real_death()
        super(Game_Attendance, self).save(*args, **kwargs)
        if (self.relevant_game.is_scheduled() or self.relevant_game.is_active()) and self.attending_character:
            self.attending_character.reveal_char_and_powers_to_player(self.relevant_game.gm)
        elif self.attending_character:
            self.attending_character.default_perms_char_and_powers_to_player(self.relevant_game.gm)

    # prevent double attendance
    class Meta:
        unique_together = (("attending_character", "relevant_game"))

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

    def notify_invitee(self, request, game):
        # This string is considered "safe" only because the markdown renderer will escape malicious HTML and scripts.
        message_body = SafeText('###{0} has invited you to an upcoming Game in {1}\n\n{2}\n\n [Click Here]({3}) to respond.'
                                .format(self.relevant_game.creator.get_username(),
                                        self.relevant_game.cell.name,
                                        self.invite_text,
                                        request.build_absolute_uri(reverse("games:games_view_game", args=[game.id])),
                                        ))
        pm_write(sender=self.relevant_game.creator,
                 recipient=self.invited_player,
                 subject= self.relevant_game.creator.get_username() + " has invited you to join " + self.relevant_game.title,
                 body=message_body,
                 skip_notification=False,
                 auto_archive=True,
                 auto_delete=False,
                 auto_moderators=None)

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(Game_Invite, self).save(*args, **kwargs)
        else:
            super(Game_Invite, self).save(*args, **kwargs)

    def invitee_can_view_scenario(self):
        return self.invited_player.has_perm("view_scenario", self.relevant_game.scenario)

class Scenario(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='scenario_creator',
        on_delete=models.PROTECT)
    title = models.CharField(max_length=130)
    summary = models.TextField(max_length=5000,
                               blank=True,
                               null=True)
    description = models.TextField(max_length=74000)
    suggested_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=HIGH_ROLLER_STATUS[0][0])
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
    tags = models.ManyToManyField("ScenarioTag",
                                   blank=True)

    def __str__(self):
        return self.title

    def is_public(self):
        public = self.tags.filter(slug="public").exists()
        return public

    def player_can_view(self, player):
        return self.is_public() or player.has_perm("view_scenario", self)

    def player_discovered(self, player):
        return Scenario_Discovery.objects.filter(relevant_scenario=self, discovering_player=player).exists()

    def choice_txt(self):
        return "{} ({}, {}-{} players)".format(self.title, self.get_suggested_status_display(), self.min_players, self.max_players)

    def finished_games(self):
        return self.game_set.filter(status__in=[GAME_STATUS[2][0], GAME_STATUS[3][0], GAME_STATUS[6][0]]).all()

    def num_finished_games(self):
        return len(self.finished_games())

    def played_discovery(self, player):
        if not player.scenario_set.filter(id=self.id).exists():
            discovery = Scenario_Discovery (
                discovering_player=player,
                relevant_scenario=self,
                reason=DISCOVERY_REASON[0][0]
            )
            discovery.save()

    def unlocked_discovery(self, player):
        if not player.scenario_set.filter(id=self.id).exists():
            discovery = Scenario_Discovery (
                discovering_player=player,
                relevant_scenario=self,
                reason=DISCOVERY_REASON[3][0]
            )
            discovery.save()

    def is_stock(self):
        return len(self.tags.all()) > 0

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(Scenario, self).save(*args, **kwargs)
            discovery = Scenario_Discovery (
                discovering_player = self.creator,
                relevant_scenario = self,
                reason = DISCOVERY_REASON[1][0]
            )
            discovery.save()
        else:
            super(Scenario, self).save(*args, **kwargs)

    class Meta:
        permissions = (
            ('edit_scenario', 'Edit scenario'),
        )


class Scenario_Discovery(models.Model):
    discovering_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                           on_delete=models.CASCADE)
    relevant_scenario = models.ForeignKey(Scenario,
                                          on_delete=models.CASCADE)
    reason = models.CharField(choices=DISCOVERY_REASON,
                             max_length=25)
    # prevent double discoveries.
    class Meta:
        unique_together = (("discovering_player", "relevant_scenario"))

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(Scenario_Discovery, self).save(*args, **kwargs)
            assign_perm('view_scenario', self.discovering_player, self.relevant_scenario)
            if self.reason == DISCOVERY_REASON[1][0]:
                assign_perm('edit_scenario', self.discovering_player, self.relevant_scenario)
        else:
            super(Scenario_Discovery, self).save(*args, **kwargs)


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
    is_charon_coin = models.BooleanField(default=False)
    is_void = models.BooleanField(default=False)
    is_journal = models.BooleanField(default=False)

    awarded_on = models.DateTimeField('awarded on')
    assigned_on = models.DateTimeField('assigned on',
                                            null=True,
                                            blank=True)

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
        self.is_void = True
        self.save()
        new_reward = Reward(relevant_game = self.relevant_game,
                            relevant_power = None,
                            rewarded_character = self.rewarded_character,
                            rewarded_player = self.rewarded_player,
                            awarded_on = self.awarded_on,
                            is_improvement = self.is_improvement,
                            is_charon_coin = self.is_charon_coin)
        new_reward.save()

    def refund_and_unassign_from_character(self):
        character = None if self.is_charon_coin or self.is_improvement else self.rewarded_character
        self.mark_void()
        new_reward = Reward(relevant_game = self.relevant_game,
                            relevant_power = None,
                            rewarded_character = character,
                            rewarded_player = self.rewarded_player,
                            awarded_on = self.awarded_on,
                            is_improvement = self.is_improvement,
                            is_charon_coin = self.is_charon_coin)
        new_reward.save()

    def mark_void(self):
        self.is_void = True
        self.save()

    def assign_to_power(self, power):
        self.relevant_power = power
        if not self.rewarded_character:
            if power.parent_power.owner:
                self.rewarded_character = power.parent_power.owner
            else:
                print("cannot assign reward to power without owner. reward, power " + str(self.id)+ " " + str(power.id))
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
            reason = ""
            if self.relevant_game.gm.id == self.rewarded_player.id:
                reason = "running "
            elif self.is_charon_coin:
                reason = "dying in "
            else:
                reason = "playing in "
            reason = reason + self.relevant_game.scenario.title
            return reason
        if self.source_asset:
            return "the Asset " + self.source_asset.relevant_asset.name
        if not self.relevant_game and self.is_charon_coin:
            return "losing a Contractor in a Side Game"


class ScenarioTag(models.Model):
    tag = models.CharField(max_length=40)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=40,
                            primary_key=True)
    def __str__(self):
        return self.tag