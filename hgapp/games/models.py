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

from hgapp.utilities import get_object_or_none

GAME_STATUS = (
    # Invites go out, players may accept invites w/ characters and change whether they are coming and with which character
    # The scenario is chosen
    # GM specifies level, message, etc.
    ('SCHEDULED', 'Scheduled'),

    # The game is "activated". invites are invalidated. Players can no longer change which character is attending
    # Characters are closed for editing for the duration of the game
    # GMs have 24 hours from this point to declare the game finished, or individual players may void their attendance.
    ('ACTIVE', 'Active'),

    # Game is finished, GM declares all outcomes, characters are unlocked or declared dead. Game is officially over
    # Void proceedings may occur. Players may open game for void vote.
    # Characters are locked while a void vote is in progress.
    # Void votes may only last 24 hours
    # GM may declare void.
    ('FINISHED', 'Finished'),

    # After a set time peroid, or after any character is attending another game that is in the "ACTIVE" state, the void window
    # is closed. The game transitions into "ARCHIVED."
    ('ARCHIVED', 'Archived'),

    # Any game that is scheduled, can be canceled, which is an end state. All invites are voided. Attendances are erased.
    ('CANCELED', 'Canceled'),

    # All games that reach the "Active" state can be voided through verious means. Attendance remains on record, but is void.
    ('VOID', 'Void'),

    # Finalized games that were entered after-the-fact.
    ('RECORDED', 'Archived'),
)

OUTCOME = (
    ('WIN', 'Victory'),
    ('LOSS', 'Loss'),
    ('DEATH', 'Died'),
    ('DECLINED', 'Declined Harbinger Invite'),
    ('RINGER_VICTORY', 'Ringer Victory'),
    ('RINGER_FAILURE', 'Ringer Failure'),
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
        return self.status == GAME_STATUS[4][0]

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
        exp_reward = ExperienceReward(
            rewarded_player=self.gm,
        )
        exp_reward.save()
        self.gm_experience_reward = exp_reward
        self.save()

    def achieves_golden_ratio(self):
        death = False
        win = False
        for attendance in self.game_attendance_set.all():
            if attendance.is_victory():
                win = True
            if attendance.is_death():
                death = True
        return win and death

    def not_attending(self, player):
        invite = get_object_or_none(self.game_invite_set.filter(invited_player=player))
        if invite:
            attendance = invite.attendance
            if attendance:
                attendance.delete()
            invite.delete()

    def get_status_blurb(self):
        if self.is_scheduled():
            return "This game is Scheduled to start " + self.scheduled_start_time.strftime('on %d, %b %Y at %I:%M %Z')
        if self.is_active():
            return "This game is Active and started " + self.actual_start_time.strftime('on %d, %b %Y at %I:%M %Z')
        if self.is_canceled():
            return "This game was Canceled and never took place."
        return "This game is " + self.get_status_display() + " and ended " + self.end_time.strftime('on %d, %b %Y at %I:%M %Z')


    def save(self, *args, **kwargs):
        if not hasattr(self, 'gm'):
            self.gm = self.creator
        if not hasattr(self, 'scenario'):
            scenario = Scenario(creator=self.gm,
                                title="Scenario for " + str(self.title),
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
                                          on_delete=models.CASCADE)

    def is_victory(self):
        return self.outcome == OUTCOME[0][0]

    def is_death(self):
        return self.outcome == OUTCOME[2][0]

    def is_ringer_victory(self):
        return self.outcome == OUTCOME[4][0]

    def associated_active_reward(self):
        return self.attending_character.reward_set.filter(relevant_game=self.relevant_game.id).filter(is_void=False).first()

    def confirm_and_reward(self):
        self.is_confirmed=True
        self.save()
        self.give_reward()

    def get_reward(self):
        return get_object_or_none(Reward, rewarded_player=self.get_player(), relevant_game=self.relevant_game, is_void=False)

    def get_player(self):
        if self.attending_character:
            return self.attending_character.player
        else:
            return self.game_invite.invited_player

    def give_reward(self):
        if not self.is_confirmed:
            return None
        if self.outcome is None:
            raise ValueError("Error, game attendane has no outcome when game is being transitioned to finished.",
                             str(self.id))
        if self.is_victory():
            player_reward = Reward(relevant_game=self.relevant_game,
                                   rewarded_character=self.attending_character,
                                   rewarded_player=self.attending_character.player,
                                   is_improvement=False)
            player_reward.save()
        if self.attending_character and not self.is_death():
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

    def save(self, *args, **kwargs):
        if self.outcome and self.attending_character and self.is_confirmed:
            # if game is finished, reveal scenario to those who brought characters.
            self.relevant_game.scenario.played_discovery(self.attending_character.player)
        if self.pk is not None:
            orig = Game_Attendance.objects.get(pk=self.pk)
            if orig.attending_character != self.attending_character:
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
        self.is_void = True
        self.save()
        new_reward = Reward(relevant_game = self.relevant_game,
                            relevant_power = None,
                            rewarded_character = character,
                            rewarded_player = self.rewarded_player,
                            awarded_on = self.awarded_on,
                            is_improvement = self.is_improvement,
                            is_charon_coin = self.is_charon_coin)
        new_reward.save()

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
        if self.relevant_game is not None:
            reason = ""
            if self.relevant_game.gm.id == self.rewarded_player.id:
                reason = "running "
            elif self.is_charon_coin:
                reason = "dying in "
            else:
                reason = "playing in "
            reason = reason + self.relevant_game.scenario.title
            return reason
        if self.source_asset is not None:
            return "the Asset " + self.source_asset.relevant_asset.name


class ScenarioTag(models.Model):
    tag = models.CharField(max_length=40)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=40,
                            primary_key=True)
    def __str__(self):
        return self.tag