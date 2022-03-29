import math

import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.utils.datetime_safe import datetime
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm
from django.utils.safestring import mark_safe
from django.db import transaction

from hgapp.utilities import get_queryset_size, get_object_or_none
from cells.models import Cell
from characters.signals import GrantAssetGift, VoidAssetGifts, AlterPortedRewards

import random
import hashlib

logger = logging.getLogger("app." + __name__)

HIGH_ROLLER_STATUS = (
    ('ANY', 'Any'),
    ('NEWBIE', 'Newbie'),
    ('NOVICE', 'Novice'),
    ('SEASONED', 'Seasoned'),
    ('VETERAN', 'Veteran'),
)

NO_PARRY_INFO = "NO_INFO"
UNAVOIDABLE = "UNAVOIDABLE"
DODGE_ONLY = "DODGE_ONLY"
UNARMED = "UNARMED"
MELEE_EDGED = "MELEE_EDGED"
MELEE_BLUNT = "MELEE_BLUNT"
BOW = "BOW"
THROWN = "THROWN"
FIREARM = "FIREARM"
ATTACK_PARRY_TYPE = (
    (NO_PARRY_INFO, "not applicable"),
    (UNAVOIDABLE, "an attack that cannot be dodged or parried"),
    (DODGE_ONLY, "an attack that can only be dodged"),
    (UNARMED, "an unarmed attack"),
    (MELEE_EDGED, "an attack with an edged melee weapon"),
    (MELEE_BLUNT, "an attack with a blunt melee weapon"),
    (BOW, "an attack with a bow or crossbow"),
    (THROWN, "an attack with a thrown weapon"),
    (FIREARM, "an attack with a firearm"),
)

NO_SPEED_INFO = "NA"
FREE_ACTION = "FREE"
QUICK_ACTION = "ACTION_QUICK"
SPLITTABLE_ACTION = "ACTION_SPLITTABLE"
COMMITTED_ACTION = "ACTION_COMMITTED"
REACTION = "REACTION"
ROLL_SPEED = (
    (NO_SPEED_INFO, "not applicable"),
    (FREE_ACTION, "a Free Action"),
    (QUICK_ACTION, "a Quick Action"),
    (SPLITTABLE_ACTION, "an Action that may be split"),
    (COMMITTED_ACTION, "a Committed Action"),
    (REACTION, "a Reaction")
)

QUIRK_CATEGORY = (
    ('PHYSICAL', 'Physical'),
    ('BACKGROUND', 'Background'),
    ('MENTAL', 'Mental'),
    ('RESTRICTED', 'Restricted'),
)

PRONOUN = (
    ('HE', 'his'),
    ('SHE', 'her'),
    ('THEY', 'their'),
)

NOT_PORTED = "NOT_PORTED"
SEASONED_PORTED = "SEASONED_PORTED"
VETERAN_PORTED = "VETERAN_PORTED"
PORT_STATUS = (
    (NOT_PORTED, "Not ported"),
    (SEASONED_PORTED, "Ported as Seasoned"),
    (VETERAN_PORTED, "Ported as Veteran"),
)

# numbers included for sorting.
MINOR_SCAR = "1MINOR"
MAJOR_SCAR = "2MAJOR"
SEVERE_SCAR = "3SEVERE"
EXTREME_SCAR = "4EXTREME"
SCAR_SEVERITY = (
    (MINOR_SCAR, "Minor Scars (Severity 4)"),
    (MAJOR_SCAR, "Major Scars (Severity 5)"),
    (SEVERE_SCAR, "Severe Scars (Severity 6)"),
    (EXTREME_SCAR, "Extreme Scars (Severity 7+)"),
)

BODY_STATUS = (
    'Scuffed',
    'Scuffed',
    'Annoyed',
    'Bruised',
    'Hurt',
    'Injured',
    'Wounded',
    'Mauled',
    'Maimed'
)

MIND_STATUS = (
    'Alert',
    'Miffed',
    'Agitated',
    'Distracted',
    'Rattled',
    'Worried',
    'Alarmed',
    'Frantic',
    'Delirious',
)

PENALTIES = (
    0,
    0,
    0,
    -1,
    -1,
    -2,
    -3,
    -4,
    "Incap",
    "Dead"
)

WEAPON_MELEE = "MELEE" # swords, clubs, axes
WEAPON_UNARMED = "UNARMED" # swords, clubs, axes
WEAPON_FIREARM = "FIREARM" # guns
WEAPON_THROWN = "THROWN" # javalins, slings, shurikens
WEAPON_PROJECTILE = "PROJECTILE" # bows, slingshots, crossbows
WEAPON_OTHER = "OTHER" # Stun guns, caltrops, etc.
WEAPON_TYPE = (
    (WEAPON_MELEE, "Melee"),
    (WEAPON_UNARMED, "Unarmed"),
    (WEAPON_FIREARM, "Firearm"),
    (WEAPON_THROWN, "Thrown"),
    (WEAPON_PROJECTILE, "Projectile"),
    (WEAPON_OTHER, "Other")
)

ART_AVAILABLE = "AVAILABLE"
ART_LOST = "LOST"
ART_DESTROYED = "DESTROYED"
ART_BROKEN = "BROKEN"
ARTIFACT_STATUS = (
    (ART_AVAILABLE, 'Available'),
    (ART_LOST, 'Lost'),
    (ART_DESTROYED, 'Destroyed'),
    (ART_BROKEN, 'Needs repair'),
)

EQUIPMENT_DEFAULT = """
Track your current equipment here. You may start with anything your Contractor would reasonably have access to. 

#### On Person

* Jeans
* T-shirt
* Wallet
* Keys
* Smartphone
* A pocket knife

#### Purple Jansport backpack

* Rain jacket
* Metal water bottle
* Toiletries kit
"""
# EXPERIENCE CONSTANTS
# These can be changed at will as the historical values are all dynamically calculated.

EXP_MVP = "MVP"
EXP_LOSS_V1 = "LOSS_V1"
EXP_LOSS_RINGER_V1 = "LOSS_RINGER_V1"
EXP_WIN_V1 = "WIN_V1"
EXP_WIN_RINGER_V1 = "WIN_RINGER_V1"
EXP_LOSS_V2 = "LOSS_V2"
EXP_LOSS_IN_WORLD_V2 = "LOSS_IN_WORLD_V2"
EXP_LOSS_RINGER_V2 = "LOSS_RINGER_V2"
EXP_WIN_V2 = "WIN_V2"
EXP_WIN_IN_WORLD_V2 = "WIN_IN_WORLD_V2"
EXP_WIN_RINGER_V2 = "WIN_RINGER_V2"
EXP_GM = "GM"
EXP_JOURNAL = "JOURNAL"
EXP_CUSTOM = "CUSTOM"
EXP_REWARD_TYPE = (
    (EXP_MVP, "earning Commission"),
    (EXP_LOSS_V1, "losing"),
    (EXP_LOSS_RINGER_V1, "losing as a ringer"),
    (EXP_WIN_V1, "winning"),
    (EXP_WIN_RINGER_V1, "winning as a ringer"),
    (EXP_LOSS_V2, "losing"),
    (EXP_LOSS_IN_WORLD_V2, "losing in-World Contract"),
    (EXP_LOSS_RINGER_V2, "losing as a ringer"),
    (EXP_WIN_V2, "winning"),
    (EXP_WIN_IN_WORLD_V2, "winning in-World Contract"),
    (EXP_WIN_RINGER_V2, "winning as a ringer"),
    (EXP_GM, "GMing"),
    (EXP_JOURNAL, "writing a journal"),
    (EXP_CUSTOM, "custom reason"),
)

EXP_REWARD_VALUES = {
    EXP_MVP: 2,
    EXP_LOSS_V1: 2,
    EXP_LOSS_RINGER_V1: 2,
    EXP_WIN_V1: 4,
    EXP_WIN_RINGER_V1: 4,
    EXP_LOSS_V2: 1,
    EXP_LOSS_IN_WORLD_V2: 3,
    EXP_LOSS_RINGER_V2: 1,
    EXP_WIN_V2: 3,
    EXP_WIN_IN_WORLD_V2: 5,
    EXP_WIN_RINGER_V2: 3,
    EXP_GM: 6,
    EXP_JOURNAL: 1,
}

EXP_NEW_CHAR = 150
EXP_COST_QUIRK_MULTIPLIER = 3
EXP_ADV_COST_ATTR_MULTIPLIER = 5
EXP_ADV_COST_SKILL_MULTIPLIER = 2
EXP_ADV_COST_SOURCE_MULTIPLIER = 2
EXP_COST_SKILL_INITIAL = 2
EXP_COST_TRAUMA_THERAPY = 3

# STAT CONSTANTS
BASE_BODY_LEVELS = 5

# PORT CONSTANTS
PORTED_GIFT_ADJUSTMENT = {
    NOT_PORTED: 0,
    SEASONED_PORTED: 15,
    VETERAN_PORTED: 30,
}
PORTED_IMPROVEMENT_ADJUSTMENT = {
    NOT_PORTED: 0,
    SEASONED_PORTED: 5,
    VETERAN_PORTED: 10,
}
PORTED_EXP_ADJUSTMENT = {
    NOT_PORTED: 0,
    SEASONED_PORTED: 90,
    VETERAN_PORTED: 180,
}

def random_string():
    return hashlib.sha224(bytes(random.randint(1, 99999999))).hexdigest()


class Character(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, blank=True)
    player = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              null=True)
    edit_secret_key = models.CharField(default = random_string,
                                              max_length=64)
    status = models.CharField(choices=HIGH_ROLLER_STATUS,
                              max_length=25,
                              default=HIGH_ROLLER_STATUS[1][0])
    appearance = models.TextField(max_length=3000)
    age = models.CharField(max_length=50)
    sex = models.CharField(max_length=15, default="Unknown")
    pronoun = models.CharField(choices=PRONOUN,
                              max_length=25,
                              default=PRONOUN[2][0])
    concept_summary = models.CharField(max_length=150)
    ambition = models.CharField(max_length=150)
    private = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    pub_date = models.DateTimeField('date published')
    edit_date = models.DateTimeField('date last edited')

    num_games = models.IntegerField(default=0)
    num_victories = models.IntegerField(default=0)
    num_losses = models.IntegerField(default=0)
    num_journals = models.IntegerField(default=0)

    ported = models.CharField(choices=PORT_STATUS,
                               max_length=50,
                               default=NOT_PORTED)

    # Optional fields
    cell = models.ForeignKey(Cell,
                              blank=True,
                              null=True,
                              on_delete=models.CASCADE)
    paradigm = models.CharField(max_length=500,
                                null=True,
                                blank=True)
    residence = models.CharField(max_length=500,
                                null=True,
                                blank=True)
    languages = models.CharField(max_length=500,
                                null=True,
                                blank=True)
    insanities = models.CharField(max_length=800,
                                null=True,
                                blank=True)
    disabilities = models.CharField(max_length=1000,
                                null=True,
                                blank=True)
    current_alias = models.CharField(max_length=300,
                                null=True,
                                blank=True)
    previous_aliases = models.CharField(max_length=500,
                                null=True,
                                blank=True)
    resources = models.CharField(max_length=500,
                                null=True,
                                blank=True)
    contacts = models.CharField(max_length=600,
                                null=True,
                                blank=True)
    equipment = models.CharField(max_length=15000,
                                null=True,
                                blank=True,
                                default=EQUIPMENT_DEFAULT)
    total_encumbrance = models.CharField(max_length=300,
                                null=True,
                                blank=True)
    max_encumbrance = models.CharField(max_length=300,
                                null=True,
                                blank=True)
    wish_list = models.CharField(max_length=1000,
                                null=True,
                                blank=True)
    to_do_list = models.TextField(max_length=5000,
                                null=True,
                                blank=True)
    contracts = models.TextField(max_length=4000,
                                null=True,
                                blank=True)
    background = models.TextField(max_length=5000,
                                null=True,
                                blank=True)
    notes = models.CharField(max_length=15000,
                                null=True,
                                blank=True)

    basic_stats = models.OneToOneField(
        'BasicStats',
        on_delete=models.CASCADE,
        null=True,
        blank=True)

    stats_snapshot = models.OneToOneField(
        'ContractStats',
        on_delete=models.CASCADE,
        null=True,
        blank=True)

    mental_damage = models.PositiveIntegerField(default=0)

    class Meta:
        permissions = (
            ('view_private_character', 'View private character'),
            ('edit_character', 'Edit character'),
        )
        indexes = [
            models.Index(fields=['num_victories', 'private']),
            models.Index(fields=['num_losses', 'private']),
            models.Index(fields=['num_games', 'private']),
            models.Index(fields=['num_journals']),
            models.Index(fields=['player']),
        ]

    def is_editable_with_key(self, key):
        if hasattr(self, 'player') and self.player:
            return False
        return self.edit_secret_key == key

    def set_default_permissions(self):
        if hasattr(self, 'player') and self.player:
            assign_perm('view_character', self.player, self)
            assign_perm('view_private_character', self.player, self)
            assign_perm('edit_character', self.player, self)
        for user in User.objects.filter(is_superuser=True).all():
            assign_perm('view_private_character', user, self)

    def reveal_character_to_player(self, player):
        assign_perm('view_character', player, self)
        assign_perm('view_private_character', player, self)

    def reveal_powers_to_player(self, player):
        for power in self.power_full_set.all():
            power.reveal_history_to_player(player)

    def default_perms_character_to_player(self, player):
        assign_perm('view_character', player, self)
        if player != self.player:
            remove_perm('view_private_character', player, self)
        else:
            assign_perm('edit_character', player, self)

    def lock_edits(self):
        if hasattr(self, 'player') and self.player:
            remove_perm('characters.edit_character', self.player)
        for power in self.power_full_set.all():
            power.lock_edits()

    def default_perms_powers_to_player(self, player):
        for power in self.power_full_set.all():
            power.default_perms_history_to_player(player)

    def reveal_char_and_powers_to_player(self, player):
        self.reveal_character_to_player(player)
        self.reveal_powers_to_player(player)

    def default_perms_char_and_powers_to_player(self, player):
        self.default_perms_character_to_player(player)
        self.default_perms_powers_to_player(player)

    def get_power_cost_total(self):
        total = 0
        for power in self.power_full_set.all():
            total = total + power.get_gift_cost()
        return total

    def world_element_cell_choices(self):
        cell_choices = set()
        if not hasattr(self, "player") or not self.player:
            return cell_choices
        queryset = self.player.cell_set.all()
        cell_choices.add(queryset)
        games_attended = self.game_set.all()
        cell_ids = set()
        for cell in queryset:
            cell_ids.add(cell.pk)
        for game in games_attended:
            if hasattr(game, "cell") and game.cell:
                cell_ids.add(game.cell.pk)
        return Cell.objects.filter(pk__in=cell_ids).all()

    def world_element_initial_cell(self):
        active_attendances = self.active_game_attendances()
        if active_attendances:
            game = active_attendances[0].relevant_game
            if hasattr(game, "cell") and game.cell:
                return game.cell
        if hasattr(self, "cell") and self.cell:
            return self.cell
        return None

    def update_contractor_journal_stats(self):
        self.num_journals = self.game_attendance_set \
            .filter(relevant_game__end_time__isnull=False, journal__isnull=False, journal__is_valid=True)\
            .count()
        self.save()

    def update_contractor_game_stats(self):
        self.update_contractor_journal_stats()
        self._update_loss_count()
        self._update_victory_count()
        self._update_game_count()
        self.status = self.calculate_status()
        self.save()

    def number_completed_games(self):
        return self.num_games if self.num_games else 0

    def _update_game_count(self):
        self.num_games = self.game_attendance_set.exclude(outcome=None, is_confirmed=False).count()

    def number_of_victories(self):
        return self.num_victories if self.num_victories else 0

    def get_contractor_status_display(self):
        return self.get_status_display() if self.ported == NOT_PORTED else self.get_ported_display()

    def get_calculated_contractor_status_display(self):
        self.status = self.calculate_status()
        return self.get_contractor_status_display()

    def _update_victory_count(self):
        self.num_victories = get_queryset_size(self.game_attendance_set.filter(is_confirmed=True, outcome="WIN"))

    def number_of_losses(self):
        return self.num_losses if self.num_losses else 0

    def _update_loss_count(self):
        self.num_losses = get_queryset_size(self.game_attendance_set.filter(is_confirmed=True, outcome="LOSS"))


    def number_completed_games_in_home_cell(self):
        if not hasattr(self, "cell") or not self.cell:
            return 0
        return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).filter(relevant_game__cell=self.cell).count()

    def number_completed_games_out_of_home_cell(self):
        if not hasattr(self, "cell") or not self.cell:
            return self.number_completed_games()
        return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).exclude(relevant_game__cell=self.cell).count()

    def calculate_status(self):
        num_victories = self.number_of_victories()
        if num_victories < 4:
            return HIGH_ROLLER_STATUS[1][0]
        elif num_victories < 10:
            return HIGH_ROLLER_STATUS[2][0]
        elif num_victories < 30:
            return HIGH_ROLLER_STATUS[3][0]
        else:
            return HIGH_ROLLER_STATUS[4][0]

    def save(self, *args, **kwargs):
        if self.ambition and self.ambition[-1] == '.':
            self.ambition = self.ambition[:-1 or None]
        if self.appearance and self.appearance[-1] == '.':
            self.appearance = self.appearance[:-1 or None]
        if self.pk is None:
            super(Character, self).save(*args, **kwargs)
            self.set_default_permissions()
            self.update_contractor_game_stats()
        else:
            self.set_default_permissions()
            super(Character, self).save(*args, **kwargs)

    def delete_char(self):
        self.is_deleted = True
        self.save()

    def player_has_cell_edit_perms(self, player):
        if self.cell:
            return self.cell.player_can_edit_characters(player)
        else:
            return False

    def player_can_edit(self, player):
        if player.is_superuser:
            return True
        if not hasattr(self, 'player') or not self.player:
            return False
        if self.is_deleted:
            return False
        can_edit = player.has_perm('edit_character', self) or self.player_has_cell_edit_perms(player)
        can_view_private = self.player_can_view(player)
        return can_edit and can_view_private

    def player_can_view(self, player):
        if player.is_superuser:
            return True
        if not hasattr(self, 'player') or not self.player:
            return True
        if self.is_deleted:
            return False
        return not self.private or player.has_perm("view_private_character", self) or self.player_has_cell_edit_perms(player)

    # Latest game last
    def completed_games(self):
        return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("relevant_game__end_time").all()

    # Latest game first
    def completed_games_rev_sort(self):
        return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("-relevant_game__end_time").all()

    def get_current_downtime_attendance(self):
        try:
            return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("-relevant_game__end_time").all()[0]
        except:
            return None

    def assigned_coin(self):
        coins = self.reward_set.filter(is_void=False, is_charon_coin=True).all()
        return coins[0] if coins else None

    def use_charon_coin(self):
        if not hasattr(self, 'player') or not self.player:
            return
        coins = self.player.rewarded_player \
            .filter(rewarded_character=None, is_charon_coin=True) \
            .filter(is_void=False).all()
        if not coins or self.assigned_coin():
            # fail silently, as players may have multiple active forms and stuff
            return
        coins[0].grant_to_character(self)

    def refund_coin(self):
        current_coin = self.assigned_coin()
        if current_coin:
            current_coin.refund_and_unassign_from_character()

    def is_dead(self):
        return self.character_death_set.filter(is_void=False).all().count() > 0

    def real_death(self):
        non_void_deaths = self.character_death_set.filter(is_void=False).all()
        if len(non_void_deaths) > 0:
            return non_void_deaths[0]
        else:
            return None

    def needs_obit(self):
        death = self.real_death()
        if death:
            return not death.obituary or len(death.obituary) == 0 or not death.cause_of_death or len(death.cause_of_death) == 0
        else:
            return False

    def void_deaths(self):
        return self.character_death_set.filter(is_void=True).all()

    def active_game_attendances(self):
        return [game for game in self.game_attendance_set.all() if game.relevant_game.is_active()]

    def scheduled_game_attendances(self):
        return [game for game in self.game_attendance_set.all() if game.relevant_game.is_scheduled()]

    def change_ported_status(self, new_ported_status):
        old_status = self.ported
        if old_status == new_ported_status:
            return
        num_gifts = PORTED_GIFT_ADJUSTMENT[new_ported_status] - PORTED_GIFT_ADJUSTMENT[self.ported]
        num_improvements = PORTED_IMPROVEMENT_ADJUSTMENT[new_ported_status] - PORTED_IMPROVEMENT_ADJUSTMENT[self.ported]
        self.ported = new_ported_status
        self.save()
        AlterPortedRewards.send_robust(sender=self.__class__,
                                       character=self,
                                       num_gifts=num_gifts,
                                       num_improvements=num_improvements)

    def show_gift_alert(self):
        return self.get_power_cost_total() != self.num_active_spent_rewards()

    def num_active_spent_rewards(self):
        return self.reward_set.filter(is_void=False).exclude(relevant_power=None).count()

    def active_rewards(self):
        return self.reward_set.filter(is_void=False).all()

    def num_active_rewards(self):
        return self.reward_set.filter(is_void=False).count()

    def spent_rewards(self):
        return self.reward_set.exclude(relevant_power=None).order_by("assigned_on", "awarded_on").all()

    def unspent_rewards(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).order_by("is_improvement", "-awarded_on").all()

    def num_unspent_rewards(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).count()

    def unspent_gifts(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).filter(is_improvement=False).order_by("-awarded_on").all()

    def num_unspent_gifts(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).filter(is_improvement=False).count()

    def unspent_improvements(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).filter(is_improvement=True).order_by("-awarded_on").all()

    def num_unspent_improvements(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).filter(is_improvement=True).count()

    def reward_cost_for_power(self, power_full):
        rewards_to_be_spent = []
        unspent_gifts = self.unspent_gifts()
        num_unspent_gifts = self.num_unspent_gifts()
        unspent_improvements = self.unspent_improvements()
        num_improvements_to_spend = 0
        if num_unspent_gifts > 0:
            rewards_to_be_spent.append(unspent_gifts[0])
        for a in range(power_full.get_gift_cost() - 1):
            if len(unspent_improvements) > a:
                num_improvements_to_spend += 1
                rewards_to_be_spent.append(unspent_improvements[a])
            elif (num_unspent_gifts > 0) and (num_unspent_gifts > (a - num_improvements_to_spend + 1)):
                rewards_to_be_spent.append(unspent_gifts[(a - num_improvements_to_spend + 1)])
            else:
                break
        return rewards_to_be_spent

    def improvement_ok(self):
        ported_adjustment = PORTED_IMPROVEMENT_ADJUSTMENT[self.ported] + PORTED_GIFT_ADJUSTMENT[self.ported]
        return self.number_of_victories() * 2 > (len(self.active_rewards()) - ported_adjustment)

    def get_powers_for_render(self):
        return self.power_full_set.all()

    def __str__(self):
        string = self.name + " ["
        if hasattr(self, 'player') and self.player:
            string = string + self.player.username + "]"
        else:
            string = string + "Anonymous User]"
        return string

    def pres_tense_to_be(self):
        if self.pronoun == PRONOUN[0][0]:
            return "He is"
        if self.pronoun == PRONOUN[1][0]:
            return "She is"
        else:
            return "They are"

    def pronoun_possessive_capitalized(self):
        if self.pronoun == PRONOUN[0][0]:
            return "His"
        if self.pronoun == PRONOUN[1][0]:
            return "Her"
        else:
            return "Their"

    def kill(self):
        if self.is_dead():
            raise ValueError("cannot kill a dead character")
        new_death = Character_Death(relevant_character=self,
                                    date_of_death=timezone.now())
        new_death.save()

    def source_values(self):
        values = {}
        for rev in self.stats_snapshot.sourcerevision_set.all():
            source = rev.relevant_source
            values[source.id] = (source.current_val, rev.max)
        return values

    def grant_initial_source_if_required(self):
        if self.stats_snapshot.sources.all().count() == 0:
            source = Source(name="Source",
                   owner=self,)
            source.save()
            new_stats = ContractStats(assigned_character=self)
            new_stats.save()
            source_rev = SourceRevision(relevant_stats = new_stats,
                                        relevant_source = source,
                                        max = 1)
            source_rev.save()
            self.regen_stats_snapshot()

    def archive_txt(self):
        output = "{}\nPlayed by: {}\nArchived on {}\n{} with {} wins and {} losses\n"
        output = output.format(self.name,
                               self.player.username if hasattr(self, "player") and self.player else "Anonymous User",
                               datetime.today(),
                               self.get_contractor_status_display(),
                               self.number_of_victories(),
                               self.number_of_losses())
        output = output + "Age: {}\nSex: {}\nAppearance: {}\nConcept: {}\nAmbition: {}\n"
        output = output.format(self.age, self.sex, self.appearance, self.concept_summary, self.ambition)
        output = output + "\n=======\nPowers:\n=======\n"
        for power_full in self.power_full_set.all():
            output = output +"{}\n"
            output = output.format(power_full.latest_archive_txt())
        return output

    def unspent_experience(self):
        total_exp = self.exp_earned()
        exp_cost = self.exp_cost()
        return int(total_exp - exp_cost)

    def exp_earned(self):
        rewards = self.experiencereward_set.filter(is_void=False).all()
        total_exp = EXP_NEW_CHAR
        for reward in rewards:
            total_exp = total_exp + reward.get_value()
        return int(total_exp) + PORTED_EXP_ADJUSTMENT[self.ported]

    def exp_cost(self):
        return self.stats_snapshot.exp_cost

    def ability_maximum(self):
        if self.status == HIGH_ROLLER_STATUS[3][0] or self.status == HIGH_ROLLER_STATUS[4][0] or self.ported != NOT_PORTED:
            return 6
        else:
            return 5

    def to_create_power_blob(self):
        return {
            "name": self.name,
            "avail_gifts": "do this",
            "avail_improvements": "do this",
            "status": self.status,
        }

    # WARNING: this is an expensive call
    def regen_stats_snapshot(self):
        self.refresh_from_db()
        stat_diffs = self.contractstats_set.filter(is_snapshot=False).order_by("id", "created_time").all()
        asset_details = []
        liability_details = []
        ability_values = []
        attribute_values = []
        limit_revisions = []
        trauma_revisions = []
        source_revisions = []
        cost = 0
        for diff in stat_diffs:
            try:
                for detail in diff.assetdetails_set.all():
                    cost = cost + diff.calc_quirk_ex_cost(detail)
                    if detail.previous_revision:
                        asset_details.remove(detail.previous_revision)
                    if not detail.is_deleted:
                        asset_details.append(detail)
                for detail in diff.liabilitydetails_set.all():
                    cost = cost - diff.calc_quirk_ex_cost(detail)
                    if detail.previous_revision:
                        liability_details.remove(detail.previous_revision)
                    if not detail.is_deleted:
                        liability_details.append(detail)
                for value in diff.attributevalue_set.all():
                    if value.relevant_attribute.is_deprecated:
                        continue
                    if value.previous_revision:
                        cost = cost + diff.calc_attr_change_ex_cost(value.previous_revision.value, value.value)
                        attribute_values.remove(value.previous_revision)
                    else:
                        cost = cost + diff.calc_attr_change_ex_cost(1, value.value)
                    attribute_values.append(value)
                for value in diff.abilityvalue_set.all():
                    if value.previous_revision:
                        cost = cost + diff.calc_ability_change_ex_cost(value.previous_revision.value, value.value)
                        ability_values.remove(value.previous_revision)
                    else:
                        cost = cost + diff.calc_ability_change_ex_cost(0, value.value)
                    if value.value > 0:
                        ability_values.append(value)
                for rev in diff.limitrevision_set.all():
                    if rev.previous_revision:
                        limit_revisions.remove(rev.previous_revision)
                    if not rev.is_deleted:
                        limit_revisions.append(rev)
                for rev in diff.traumarevision_set.all():
                    cost = cost + diff.calc_trauma_xp_cost(rev)
                    if rev.previous_revision:
                        trauma_revisions.remove(rev.previous_revision)
                    if not rev.is_deleted:
                        trauma_revisions.append(rev)
                for rev in diff.sourcerevision_set.all():
                    if rev.previous_revision:
                        source_revisions.remove(rev.previous_revision)
                        cost = cost + diff.calc_source_change_ex_cost(rev.previous_revision.max, rev.max)
                    else:
                        cost = cost + diff.calc_source_change_ex_cost(1, rev.max)
                    source_revisions.append(rev)
            except ValueError as e:
                logger.error('Error regenerating stats snapshot. stats_diff: %s\n\n stats_diffs: %s\n\n exception: %s',
                             str(diff),
                             str(stat_diffs),
                             str(e))
                raise e

        self.stats_snapshot.clear()
        for deet in asset_details:
            snapshot_deet = AssetDetails(
                relevant_stats=self.stats_snapshot,
                relevant_asset=deet.relevant_asset,
                details=deet.details,
                previous_revision=deet,
            )
            snapshot_deet.save()
        for deet in liability_details:
            snapshot_deet = LiabilityDetails(
                relevant_stats=self.stats_snapshot,
                relevant_liability=deet.relevant_liability,
                details=deet.details,
                previous_revision=deet,
            )
            snapshot_deet.save()
        for value in ability_values:
            snapshot_value = AbilityValue(
                relevant_stats=self.stats_snapshot,
                relevant_ability=value.relevant_ability,
                value=value.value,
                previous_revision=value,
            )
            snapshot_value.save()
        for value in attribute_values:
            snapshot_value = AttributeValue(
                relevant_stats=self.stats_snapshot,
                relevant_attribute=value.relevant_attribute,
                value=value.value,
                previous_revision=value,
            )
            snapshot_value.save()
        for rev in limit_revisions:
            snapshot_rev = LimitRevision(
                relevant_stats=self.stats_snapshot,
                relevant_limit=rev.relevant_limit,
                previous_revision=rev,
            )
            snapshot_rev.save()
        for rev in trauma_revisions:
            snapshot_rev = TraumaRevision(
                relevant_stats=self.stats_snapshot,
                relevant_trauma=rev.relevant_trauma,
                previous_revision=rev,
            )
            snapshot_rev.save()
        for rev in source_revisions:
            snapshot_rev = SourceRevision(
                relevant_stats=self.stats_snapshot,
                relevant_source=rev.relevant_source,
                previous_revision=rev,
                max=rev.max,
            )
            snapshot_rev.save()
        self.stats_snapshot.exp_cost = cost
        self.stats_snapshot.save()

    def num_body_levels(self):
        brawn_value = self.stats_snapshot.attributevalue_set.get(relevant_attribute__scales_body=True).val_with_bonuses()
        return BASE_BODY_LEVELS + math.ceil(brawn_value / 2)

    def num_mind_levels(self):
        mind_scaling_attrs = self.stats_snapshot.attributevalue_set.filter(relevant_attribute__scales_mind=True).all()
        mind_val = 1
        for attr in mind_scaling_attrs:
            mind_val = mind_val + attr.val_with_bonuses()
        if mind_val <= 3:
            return 3
        elif mind_val >= 9:
            return 9
        else:
            return mind_val

    def get_attribute_values_by_id(self):
        if not self.stats_snapshot:
            return {}
        attributes = self.get_attributes()
        attribute_val_by_id = {}
        for attr in attributes:
            attribute_val_by_id[attr.relevant_attribute.id] = attr.value
        return attribute_val_by_id

    def get_ability_values_by_id(self):
        if not self.stats_snapshot:
            return {}
        ability_val_by_id = {}
        char_ability_values = self.stats_snapshot.abilityvalue_set.all()
        for x in char_ability_values:
            ability_val_by_id[x.relevant_ability.id] = x.value
        return ability_val_by_id

    def get_attributes(self, is_physical=None):
        query = self.stats_snapshot.attributevalue_set \
            .prefetch_related('relevant_attribute')
        if is_physical is not None:
            query = query.filter(relevant_attribute__is_physical=is_physical)
        return query.order_by('relevant_attribute__name').all()

    def get_abilities(self):
        return self.stats_snapshot.abilityvalue_set \
            .prefetch_related('relevant_ability') \
            .order_by('relevant_ability__name')\
            .all()

    def get_health_display(self):
        # Example output for bottom 3 rows.
        # format is: (injury flavor, body box id or 'none', penalty, mind box id or 'none', mental health flavor)
        # ('maimed', '4', '-4', '5', 'delerious')
        # ('', '5', 'Incapacitated', '6', '')   # incap
        # ('', '6', 'Dead', 'none', '')   # dead level
        body_levels = self.num_body_levels()
        mind_levels = self.num_mind_levels()
        health_rows = []
        for x in range(max(body_levels, mind_levels) + 1):
            health_rows.insert(0, (
                BODY_STATUS[-(x - 1)] if BODY_STATUS[-(x - 2)] and x-2 >= 0 and x <= body_levels else "",
                body_levels - x if x <= body_levels else 'none',
                PENALTIES[-x-1],
                mind_levels - x if x <= mind_levels and x > 0 else 'none',
                MIND_STATUS[-(x - 1)] if MIND_STATUS[-(x - 2)] and x - 2 >= 0 and x <= mind_levels else "",
            ))
        return health_rows

    def get_bonus_for_attribute(self, attribute):
        existing_bonus = get_object_or_none(AttributeBonus, character=self, attribute=attribute)
        return existing_bonus.value if existing_bonus else 0

    def set_bonus_for_attribute(self, attribute, value):
        existing_bonus = get_object_or_none(AttributeBonus, character=self, attribute=attribute)
        if existing_bonus:
            existing_bonus.value = value
            existing_bonus.save()
        else:
            new_bonus = AttributeBonus(character=self,
                                       attribute=attribute,
                                       value=value)
            new_bonus.save()

    def reset_attribute_bonuses(self):
        attributes = self.stats_snapshot.attributevalue_set.all()
        for attribute in attributes:
            self.set_bonus_for_attribute(attribute.relevant_attribute, 0)
        powers = self.power_full_set.all()
        bonus_by_attribute = {}
        for power in powers:
            bonuses = power.latest_revision().get_attribute_bonuses()
            for attr, bonus in bonuses:
                curr_bonus = bonus_by_attribute.get(attr, 0)
                if bonus > curr_bonus:
                    bonus_by_attribute[attr] = bonus
        for attribute_value in attributes:
            attr = attribute_value.relevant_attribute
            if attr in bonus_by_attribute:
                self.set_bonus_for_attribute(attr, bonus_by_attribute.get(attr))


class StockBattleScar(models.Model):
    type = models.CharField(choices=SCAR_SEVERITY,
                            max_length=45,
                            default=MINOR_SCAR)
    description = models.CharField(max_length=500)
    system = models.CharField(max_length=500)


class BattleScar(models.Model):
    character = models.ForeignKey(Character,
                                   on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
    system = models.CharField(max_length=500, blank=True)


class WorldElement(models.Model):
    # owning character
    # null for sig items without owners
    character = models.ForeignKey(Character, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=5000)
    system = models.CharField(max_length=1000, blank=True)

    # when cell is null, element is created by gift system
    cell = models.ForeignKey(Cell,
                             blank=True,
                             null=True,
                             on_delete=models.CASCADE)


    def __str__(self):
        return self.name

    class Meta:
        abstract = True

class Condition(WorldElement):
    pass

class Circumstance(WorldElement):
    pass


class Artifact(WorldElement):
    # Signature Items created
    crafting_character = models.ForeignKey(Character, related_name="creator", on_delete=models.CASCADE, null=True)
    creating_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                        on_delete=models.CASCADE,
                                        null=True)
    is_consumable = models.BooleanField(default=False)
    is_signature = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=1000, default="", blank=True)
    availability = models.CharField(choices=ARTIFACT_STATUS, max_length=55, default=ART_AVAILABLE)


class Injury(models.Model):
    character = models.ForeignKey(Character,
                                   on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
    is_stabilized = models.BooleanField(default=False)
    severity = models.PositiveIntegerField(default=1)


class BasicStats(models.Model):
    stats = models.CharField(max_length=10000)
    advancement_history = models.TextField(max_length=10000,
                                null=True,
                                blank=True)
    movement = models.CharField(max_length=500,
                                null=True,
                                blank=True)
    armor = models.CharField(max_length=300,
                                null=True,
                                blank=True)

## EXPERIENCE
class ExperienceReward(models.Model):
    created_time = models.DateTimeField(default=timezone.now)
    rewarded_character = models.ForeignKey(Character,
                                           blank=True,
                                           null=True,
                                           on_delete=models.CASCADE)
    rewarded_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                        on_delete=models.CASCADE)
    type = models.CharField(choices=EXP_REWARD_TYPE,
                            max_length=45,
                            default=EXP_MVP)
    is_void = models.BooleanField(default=False)
    custom_reason = models.CharField(max_length=150, blank=True, null=True)
    custom_value = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['rewarded_character', 'created_time']),
            models.Index(fields=['rewarded_character', 'is_void', 'type']),
            models.Index(fields=['rewarded_player', 'rewarded_character']),
        ]

    def mark_void(self):
        self.is_void = True
        self.save()

    def source_blurb(self):
        if hasattr(self, 'custom_reason') and self.custom_reason:
            return mark_safe(self.custom_reason)
        reason = "from {}".format(self.get_type_display())
        if self.type == EXP_GM:
            return "{} {}".format(reason, self.game.scenario.title)
        if self.type == EXP_JOURNAL:
            return mark_safe(reason)
        if hasattr(self, 'game_attendance'):
            attendance = self.game_attendance
            return "{} {}".format(reason, attendance.relevant_game.scenario.title)
        if hasattr(self, 'mvp_exp_attendance'):
            attendance = self.mvp_exp_attendance
            return "{} in {}".format(reason, attendance.relevant_game.scenario.title)
        else:
            self.log_bad_source()
            raise ValueError("Experience reward has bad source: " + str(self.pk))

    def get_value(self):
        if self.is_void:
            return 0
        if hasattr(self, 'custom_value') and self.custom_value:
            return self.custom_value
        if self.type == EXP_CUSTOM:
            return 0
        return EXP_REWARD_VALUES[self.type]

    def log_bad_source(self):
        logger.error('Experience reward %s for character %s has no source.', str(self.pk), str(self.rewarded_character))

    def get_history_blurb(self):
        value = self.get_value()
        source_text = self.source_blurb()
        return ("+{0} Exp.".format(str(value)), "{0}".format(source_text))

## ADVANCED STATS
class Trait(models.Model):
    name = models.CharField(max_length=50)
    tutorial_text = models.CharField(max_length=250,
                              null=True,
                              blank=True)
    is_physical = models.BooleanField(default=False) # for rendering character sheet

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

    def __lt__(self, other):
        return self.name < other.name

class Attribute(Trait):
    scales_body = models.BooleanField(default=False)
    scales_mind = models.BooleanField(default=False)
    is_deprecated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        existing = get_object_or_none(Attribute, pk=self.pk)
        super().save(*args, **kwargs)
        if existing and (existing.is_deprecated != self.is_deprecated):
            characters = Character.objects.all()
            for character in characters:
                try:
                    with transaction.atomic():
                        character.regen_stats_snapshot()
                except Exception as inst:
                    logger.error('Error regenerating stats snapshot for character %s id %s',
                                 str(character.name),
                                 str(character.id))
                    logger.exception(inst)



class Ability(Trait):
    is_primary = models.BooleanField(default=False)

class Roll(models.Model):
    attribute = models.ForeignKey(Attribute,
                                  on_delete=models.CASCADE,
                                  null=True)
    ability = models.ForeignKey(Ability,
                                on_delete=models.CASCADE,
                                null=True)
    is_mind = models.BooleanField(default=False)
    is_body = models.BooleanField(default=False)
    parry_type = models.CharField(choices=ATTACK_PARRY_TYPE,
                                  max_length=30,
                                  default=NO_PARRY_INFO)
    speed = models.CharField(choices=ROLL_SPEED,
                             max_length=30,
                             default=NO_SPEED_INFO)
    difficulty = models.PositiveIntegerField(default=6)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['attribute', 'ability', 'difficulty', 'is_mind', 'is_body', 'parry_type', 'speed'], name='unique_roll'),
            models.UniqueConstraint(fields=['is_mind', 'difficulty', 'parry_type', 'speed'], condition=Q(is_mind=True), name='one_mind_roll'),
            models.UniqueConstraint(fields=['is_body', 'difficulty', 'parry_type', 'speed'], condition=Q(is_body=True), name='one_body_roll'),
        ]
        indexes = [
            models.Index(fields=['is_mind', 'difficulty']),
            models.Index(fields=['is_body', 'difficulty']),
            models.Index(fields=['attribute', 'ability', 'difficulty',]),
        ]

    def __str__(self):
        supp_info = None
        if self.parry_type != NO_PARRY_INFO:
            supp_info = "(defended against as {})".format(self.get_parry_type_display())
        if self.speed != NO_SPEED_INFO:
            speed = "as {}".format(self.get_speed_display())
            supp_info = "{} {}".format(speed, supp_info) if supp_info else speed
        return "{}, Diff {}{}".format(self.get_main_roll_component(), self.difficulty, " " + supp_info if supp_info else "")

    def get_main_roll_component(self):
        if hasattr(self, "attribute") and self.attribute:
            main_component = self.attribute.name
        else:
            main_component = "Mind" if self.is_mind else "Body"
        if hasattr(self, "ability") and self.ability:
            ability_name = self.ability.name
            roll = "{} + {}".format(main_component, ability_name)
        else:
            roll = main_component
        return roll


    def render_html_for_current_contractor(self):
        if self.parry_type != NO_PARRY_INFO:
            return self.get_defense_text()
        html_output = "{}" \
        "<span>" \
            "<span class=\"js-roll-value\" style=\"display:none;\">" \
                " (<span class=\"js-roll-num-dice\" " \
                "data-attr-id=\"{}\" " \
                "data-ability-id=\"{}\" " \
                "data-is-mind=\"{}\" " \
                "data-is-body=\"{}\">" \
                "</span>" \
                "<span class=\"js-roll-penalty\" style=\"color:#fb7e48;\"></span>" \
            " dice)</span>" \
            " Difficulty <span class=\"js-roll-difficulty\" data-difficulty=\"{}\">{}</span>" \
        "</span>" \
        .format(self.get_main_roll_component(),
                self.attribute.id if hasattr(self, "attribute") and self.attribute else " ",
                self.ability.id if hasattr(self, "ability") and self.ability else " ",
                self.is_mind,
                self.is_body,
                self.difficulty,
                self.difficulty)
        roll_text = mark_safe(html_output)
        if self.speed != NO_SPEED_INFO:
            roll_text = "{} as {}".format(roll_text, self.get_speed_display())
        return roll_text

    def render_value_for_power(self):
        if self.parry_type != NO_PARRY_INFO:
            return self.get_defense_text()
        first_word = "Mind" if self.is_mind else "Body" if self.is_body else self.attribute.name
        if self.ability:
            roll_text = "{} + {}".format(first_word, self.ability.name)
        else:
            roll_text = first_word
        roll_text = "{}, Difficulty {}".format(roll_text, self.difficulty)
        if self.speed != NO_SPEED_INFO:
            roll_text = "{} as {}".format(roll_text, self.get_speed_display())
        return roll_text

    def get_defense_text(self):
        if self.parry_type == DODGE_ONLY:
            roll_text = "to dodge"
        else:
            roll_text = "to dodge or parry (as for {})".format(self.get_parry_type_display())
        if self.speed != NO_SPEED_INFO:
            roll_text = "{} as {}".format(roll_text, self.get_speed_display())
        return roll_text

    # To obtain the singleton rolls, use this static getter methods instead of directly creating the roll objects.
    @staticmethod
    def get_mind_roll(difficulty=6, parry_type=NO_PARRY_INFO, speed=FREE_ACTION):
        mind_roll = get_object_or_none(Roll, is_mind=True, difficulty=difficulty, parry_type=parry_type, speed=speed)
        if mind_roll:
            return mind_roll
        else:
            mind_roll = Roll(is_mind=True, difficulty=difficulty, parry_type=parry_type, speed=speed)
            mind_roll.save()
            return mind_roll

    @staticmethod
    def get_body_roll(difficulty=6, parry_type=NO_PARRY_INFO, speed=FREE_ACTION):
        body_roll = get_object_or_none(Roll, is_body=True, difficulty=difficulty, parry_type=parry_type, speed=speed)
        if body_roll:
            return body_roll
        else:
            mind_roll = Roll(is_body=True, difficulty=difficulty, parry_type=parry_type, speed=speed)
            mind_roll.save()
            return mind_roll

    @staticmethod
    def get_roll(attribute=None, ability=None, difficulty=6, parry_type=NO_PARRY_INFO, speed=NO_SPEED_INFO):
        roll = get_object_or_none(Roll,
                                  attribute=attribute,
                                  ability=ability,
                                  is_mind=False,
                                  is_body=False,
                                  difficulty=difficulty,
                                  parry_type=parry_type,
                                  speed=speed)
        if roll:
            return roll
        else:
            roll = Roll(attribute=attribute,
                        ability=ability,
                        is_mind=False,
                        is_body=False,
                        difficulty=difficulty,
                        parry_type=parry_type,
                        speed=speed)
            roll.save()
            return roll


class Weapon(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(choices=WEAPON_TYPE,
                            max_length=30,
                            default=WEAPON_MELEE)
    bonus_damage = models.IntegerField(default=0)
    damage_errata = models.CharField(max_length=300, blank=True) # errata displayed directly after damage
    attack_roll = models.ForeignKey(Roll,
                                    blank=True,
                                    null=True,
                                    on_delete=models.CASCADE)
    # intended to use instead of attack_roll for daggers. Can also be used as addendum for discretionary Difficulty.
    attack_roll_text = models.CharField(max_length=300, blank=True)
    attack_system_text = models.CharField(max_length=300, blank=True,
                                          help_text="If no actual roll is specified, use this in power system text")
    range = models.CharField(max_length=300, blank=True)
    errata = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return self.name + "(" + self.type + ")"

    def attack_roll_replacement(self):
        if self.attack_roll:
            attack_roll = self.attack_roll.render_value_for_power()
        elif self.attack_system_text:
            attack_roll = self.attack_system_text
        else:
            attack_roll = "UNDEFINED"
        return attack_roll


class Quirk(models.Model):
    name = models.CharField(max_length=150)
    value = models.PositiveIntegerField()
    description = models.CharField(max_length=2000)
    system = models.CharField(max_length=2000) # A "just the facts" summary
    is_public = models.BooleanField(default=True)
    category = models.CharField(choices=QUIRK_CATEGORY,
                              max_length=50,
                              default=QUIRK_CATEGORY[1][0])
    eratta = models.CharField(max_length=2500,
                              blank = True,
                              null = True)
    details_field_name = models.CharField(max_length=150,
                              blank = True,
                              null = True)
    multiplicity_allowed = models.BooleanField(default=False)
    grants_gift = models.BooleanField(default=False)

    def is_physical(self):
        return self.category == QUIRK_CATEGORY[0][0]

    def is_background(self):
        return self.category == QUIRK_CATEGORY[1][0]

    def is_mental(self):
        return self.category == QUIRK_CATEGORY[2][0]

    def is_restricted(self):
        return self.category == QUIRK_CATEGORY[3][0]

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

class Asset(Quirk):
    def is_liability(self):
        return False

class Liability(Quirk):
    def is_liability(self):
        return True

class Trauma(models.Model):
    description = models.CharField(max_length=500)

class Source(models.Model):
    name = models.CharField(max_length=500)
    owner = models.ForeignKey(Character,
                              on_delete=models.CASCADE)
    current_val = models.PositiveIntegerField(default = 1) # Max val is stored on the revision

class Limit(models.Model):
    name = models.CharField(max_length=40)
    description = models.CharField(max_length=1000)
    is_default = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    # if not a primary, should have an owner.
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              null=True,
                              blank=True,
                              on_delete=models.CASCADE)

class ContractStats(models.Model):
    created_time = models.DateTimeField(default=timezone.now)
    is_snapshot = models.BooleanField(default=False)
    assigned_character = models.ForeignKey(Character, on_delete=models.CASCADE)
    exp_cost = models.IntegerField(default=-1)

    attributes = models.ManyToManyField(Attribute,
                                       blank=True,
                                       through="AttributeValue",
                                       through_fields=('relevant_stats', 'relevant_attribute'))
    abilities = models.ManyToManyField(Ability,
                                       blank=True,
                                       through="AbilityValue",
                                       through_fields= ('relevant_stats', 'relevant_ability'))
    assets = models.ManyToManyField(Asset,
                                   blank=True,
                                   through="AssetDetails",
                                   through_fields=('relevant_stats', 'relevant_asset'))
    liabilities = models.ManyToManyField(Liability,
                                   blank=True,
                                   through="LiabilityDetails",
                                   through_fields=('relevant_stats', 'relevant_liability'))
    limits = models.ManyToManyField(Limit,
                                    through="LimitRevision",
                                    through_fields=('relevant_stats', 'relevant_limit'),
                                    blank=True)
    traumas = models.ManyToManyField(Trauma,
                                    through="TraumaRevision",
                                    through_fields=('relevant_stats', 'relevant_trauma'),
                                    blank=True)
    sources = models.ManyToManyField(Source,
                                    through="SourceRevision",
                                    through_fields=('relevant_stats', 'relevant_source'),
                                    blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['assigned_character', 'is_snapshot'], name='stats_char_idx'),
            models.Index(fields=['created_time'], name='stats_date_idx'),
        ]

    def calc_attr_change_ex_cost(self, old_value, new_value):
        return ((new_value - old_value) * (old_value + new_value - 1) / 2) * EXP_ADV_COST_ATTR_MULTIPLIER

    def calc_source_change_ex_cost(self, old_value, new_value):
        return ((new_value - old_value) * (old_value + new_value - 1) / 2) * EXP_ADV_COST_SOURCE_MULTIPLIER

    def calc_quirk_ex_cost(self, quirk_details):
        if quirk_details.is_deleted:
            return - EXP_COST_QUIRK_MULTIPLIER * quirk_details.relevant_quirk().value
        if quirk_details.previous_revision:
            return 0
        else:
            return EXP_COST_QUIRK_MULTIPLIER * quirk_details.relevant_quirk().value

    def calc_ability_change_ex_cost(self, old_value, new_value):
        if old_value == 0 and new_value != 0:
            initial_cost = 2
        elif old_value != 0 and new_value == 0:
            initial_cost = -2
        else:
            initial_cost = 0
        return ((new_value - old_value) * (old_value + new_value - 1) / 2) * EXP_ADV_COST_SKILL_MULTIPLIER + initial_cost


    def calc_trauma_xp_cost(self, trauma_revision):
        if trauma_revision.is_deleted and trauma_revision.was_bought_off:
            return EXP_COST_TRAUMA_THERAPY
        return 0

    def get_exp_phrase(self, exp_cost):
        change_sign = "+" if exp_cost < 0 else "-"
        return  "{0}{1:d}:".format(change_sign, abs(int(exp_cost)))

    def get_trait_value_change_phrase(self, trait_name, exp_cost, prev_value, new_value):
        return "{0} {1} from {2} to {3}".format(
            trait_name,
            "raised" if exp_cost > 0 else "lowered",
            str(prev_value),
            str(new_value))

    # This is an expensive call
    def get_change_phrases(self):
        change_phrases = []
        for attribute in self.attributevalue_set.all():
            if attribute.relevant_attribute.is_deprecated:
                continue
            exp_cost = self.calc_attr_change_ex_cost(attribute.previous_revision.value, attribute.value)
            exp_phrase = self.get_exp_phrase(exp_cost)
            phrase = self.get_trait_value_change_phrase(attribute.relevant_attribute.name,
                                                        exp_cost,
                                                        attribute.previous_revision.value,
                                                        attribute.value)
            change_phrases.append((exp_phrase, phrase,))
        for ability in self.abilityvalue_set.all():
            prev_value = ability.previous_revision.value if ability.previous_revision else 0
            exp_cost = self.calc_ability_change_ex_cost(prev_value, ability.value)
            exp_phrase = self.get_exp_phrase(exp_cost)
            phrase = self.get_trait_value_change_phrase(ability.relevant_ability.name,
                                                        exp_cost,
                                                        prev_value,
                                                        ability.value)
            change_phrases.append((exp_phrase, phrase,))
        for asset in self.assetdetails_set.all():
            exp_cost = self.calc_quirk_ex_cost(asset)
            exp_phrase = self.get_exp_phrase(exp_cost)
            change_word = "removed" if asset.is_deleted else \
                "changed {0} of ".format(asset.relevant_quirk().details_field_name) if asset.previous_revision else "purchased"
            phrase = "{0} asset {1} {2}".format(
                change_word,
                asset.relevant_quirk().name,
                "(from \"{0}\" to \"{1}\")".format(asset.previous_revision.details, asset.details) \
                    if asset.previous_revision and not asset.is_deleted else \
                    "({0})".format(asset.details) if asset.details else ""
            )
            change_phrases.append((exp_phrase, phrase,))
        for liability in self.liabilitydetails_set.all():
            exp_cost = - self.calc_quirk_ex_cost(liability)
            exp_phrase = self.get_exp_phrase(exp_cost)
            change_word = "removed" if liability.is_deleted else \
                "changed {0} of ".format(liability.relevant_quirk().details_field_name) if liability.previous_revision else "took"
            phrase = "{0} liability {1} {2}".format(
                change_word,
                liability.relevant_quirk().name,
                "(from \"{0}\" to \"{1}\")".format(liability.previous_revision.details, liability.details) \
                    if liability.previous_revision and not liability.is_deleted else \
                    "({0})".format(liability.details) if liability.details else ""
            )
            change_phrases.append((exp_phrase, phrase,))
        for limit in self.limitrevision_set.all():
            exp_cost = 0
            exp_phrase = self.get_exp_phrase(exp_cost)
            change_word = "removed" if limit.is_deleted else \
                "edited" if limit.previous_revision else "took"
            phrase = "{0} Limit {1}".format(
                change_word,
                limit.relevant_limit.name
            )
            change_phrases.append((exp_phrase, phrase,))
        for trauma in self.traumarevision_set.all():
            exp_cost = self.calc_trauma_xp_cost(trauma)
            exp_phrase = self.get_exp_phrase(exp_cost)
            change_word = "therapy for" if trauma.is_deleted and trauma.was_bought_off else \
                "cured" if trauma.is_deleted else "developed"
            phrase = "{0} Trauma {1}".format(
                change_word,
                trauma.relevant_trauma.description
            )
            change_phrases.append((exp_phrase, phrase,))
        for source in self.sourcerevision_set.all():
            if source.previous_revision:
                exp_cost = self.calc_source_change_ex_cost(source.previous_revision.max, source.max)
                exp_phrase = self.get_exp_phrase(exp_cost)
                if source.max == source.previous_revision.max:
                    phrase = "Source renamed to " + source.relevant_source.name
                else:
                    phrase = self.get_trait_value_change_phrase(source.relevant_source.name,
                                                                exp_cost,
                                                                source.previous_revision.max,
                                                                source.max)
                change_phrases.append((exp_phrase, phrase,))
        return change_phrases

    def clear(self):
        if not self.is_snapshot:
            raise ValueError("should only clear snapshots")
        for asset in self.assetdetails_set.all():
            asset.delete()
        for liability in self.liabilitydetails_set.all():
            liability.delete()
        for ability in self.abilityvalue_set.all():
            ability.delete()
        for attribute in self.attributevalue_set.all():
            attribute.delete()
        for limit in self.limitrevision_set.all():
            limit.delete()
        for trauma in self.traumarevision_set.all():
            trauma.delete()
        for source in self.sourcerevision_set.all():
            source.delete()
        self.save()


class QuirkDetails(models.Model):
    relevant_stats = models.ForeignKey(ContractStats,
                                       on_delete=models.CASCADE)
    details = models.CharField(max_length=2000,
                                null=True,
                                blank=True)
    previous_revision = models.ForeignKey('self', # Used in revisioning to determine if this quirk is an edit or an add
                               null=True,
                               blank=True,
                               on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False) # used in revisioning to determine if this quirk was deleted.

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.previous_revision:
            if self.previous_revision.relevant_stats.is_snapshot:
                raise ValueError("A Quirk's parent revision cannot be owned by a snapshot.")
        super(QuirkDetails, self).save(*args, **kwargs)

class AssetDetails(QuirkDetails):
    relevant_asset = models.ForeignKey(Asset,
                                       on_delete=models.CASCADE)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.previous_revision and self.is_deleted and self.relevant_asset.grants_gift:
            VoidAssetGifts.send_robust(sender=self.__class__,
                                  assetDetail=self,
                                  character=self.relevant_stats.assigned_character)
        if not self.previous_revision and not self.is_deleted and self.relevant_asset.grants_gift:
            GrantAssetGift.send_robust(sender=self.__class__,
                                  assetDetail=self,
                                  character=self.relevant_stats.assigned_character)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

    def relevant_quirk(self):
        return self.relevant_asset

class LiabilityDetails(QuirkDetails):
    relevant_liability = models.ForeignKey(Liability,
                                       on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

    def relevant_quirk(self):
        return self.relevant_liability


class TraitValue(models.Model):
    relevant_stats = models.ForeignKey(ContractStats,
                                             on_delete=models.CASCADE)
    value = models.PositiveIntegerField()
    previous_revision = models.ForeignKey('self',
                                           null=True,
                                           blank=True,
                                           on_delete=models.CASCADE) # Used in revisioning to determine value change.
    class Meta:
        abstract = True

    def get_class(self):
        return TraitValue

    def save(self, *args, **kwargs):
        if self.previous_revision:
            if self.previous_revision.relevant_stats.is_snapshot:
                raise ValueError("A Trait's parent revision cannot be owned by a snapshot.")
        if hasattr(self, "previous_revision") and self.previous_revision and not self.relevant_stats.is_snapshot:
            if self.get_class().objects.filter(previous_revision=self.previous_revision,
                                           relevant_stats__is_snapshot=False).exists():
                raise ValueError("No two non-snapshots can have the same previous revision")
        super(TraitValue, self).save(*args, **kwargs)




class AttributeValue(TraitValue):
    relevant_attribute = models.ForeignKey(Attribute,
                                       on_delete=models.CASCADE)

    class Meta:
        unique_together = (("relevant_attribute", "relevant_stats"))
        indexes = [
            models.Index(fields=['relevant_stats']),
            models.Index(fields=['previous_revision']),
        ]

    def val_with_bonuses(self):
        return self.value + self.relevant_stats.assigned_character.get_bonus_for_attribute(attribute=self.relevant_attribute)

    def get_class(self):
        return AttributeValue


class AbilityValue(TraitValue):
    relevant_ability = models.ForeignKey(Ability,
                                       on_delete=models.CASCADE)
    class Meta:
        unique_together = (("relevant_ability", "relevant_stats"))
        indexes = [
            models.Index(fields=['relevant_stats']),
            models.Index(fields=['previous_revision']),
        ]

    def get_class(self):
        return AbilityValue


class LimitRevision(models.Model):
    relevant_limit = models.ForeignKey(Limit,
                                       on_delete=models.CASCADE)
    relevant_stats = models.ForeignKey(ContractStats,
                                             on_delete=models.CASCADE)
    previous_revision = models.ForeignKey('self',
                                          null=True,
                                          blank=True,
                                          on_delete=models.CASCADE)  # Used in revisioning to determine value change.
    is_deleted = models.BooleanField(default=False)
    class Meta:
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

class TraumaRevision(models.Model):
    relevant_trauma = models.ForeignKey(Trauma,
                                        on_delete=models.CASCADE)
    relevant_stats = models.ForeignKey(ContractStats,
                                             on_delete=models.CASCADE)
    previous_revision = models.ForeignKey('self',
                                          null=True,
                                          blank=True,
                                          on_delete=models.CASCADE)  # Used in revisioning to determine value change.
    is_deleted = models.BooleanField(default=False)
    was_bought_off = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

    def save(self, *args, **kwargs):
        if hasattr(self, "previous_revision") and self.previous_revision and not self.relevant_stats.is_snapshot:
            if TraumaRevision.objects.filter(previous_revision=self.previous_revision, relevant_stats__is_snapshot=False).exists():
                raise ValueError("No two non-snapshots can have the same previous revision")
        super(TraumaRevision, self).save(*args, **kwargs)


class SourceRevision(models.Model):
    relevant_source = models.ForeignKey(Source,
                                        on_delete=models.CASCADE)
    relevant_stats = models.ForeignKey(ContractStats,
                                             on_delete=models.CASCADE)
    previous_revision = models.ForeignKey('self',
                                          null=True,
                                          blank=True,
                                          on_delete=models.CASCADE)  # Used in revisioning to determine value change.
    max = models.PositiveIntegerField()

    class Meta:
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

class Character_Death(models.Model):
    relevant_character = models.ForeignKey(Character,
                                           on_delete=models.CASCADE)
    is_void = models.BooleanField(default=False)
    obituary = models.CharField(max_length=10000,
                                null=True,
                                blank=True)
    date_of_death = models.DateTimeField('date of death')
    cause_of_death= models.CharField(max_length=200,
                                     null=True,
                                     blank=True)

    def mark_void(self):
        self.is_void = True
        self.save()


class Graveyard_Header(models.Model):
    header = models.TextField()

    def _str_(self):
        return self.header


class CharacterTutorial(models.Model):
    core_info = models.TextField(max_length=3000)
    attributes = models.TextField(max_length=3000)
    attributes_view = models.TextField(max_length=3000)
    abilities = models.TextField(max_length=3000)
    abilities_view = models.TextField(max_length=3000)
    secondary_abilities = models.TextField(max_length=3000)
    assets_and_liabilities = models.TextField(max_length=3000)
    limits = models.TextField(max_length=3000)
    limits_view = models.TextField(max_length=3000)
    traumas = models.TextField(max_length=3000)
    injuries = models.TextField(max_length=3000)
    battle_scars = models.TextField(max_length=3000)
    penalty = models.TextField(max_length=3000)
    mind = models.TextField(max_length=3000)
    body = models.TextField(max_length=3000)
    wound = models.TextField(max_length=3000, default="placeholder")
    source_edit = models.TextField(max_length=3000)
    source_view = models.TextField(max_length=3000)
    experience_edit = models.TextField(max_length=3000)
    equipment = models.TextField(max_length=3000)
    character_timeline = models.TextField(max_length=3000)
    powers_view = models.TextField(max_length=3000)
    exert_mind = models.TextField(max_length=3000)
    recover_mind = models.TextField(max_length=3000)
    exert_body = models.TextField(max_length=3000)
    charon_coin = models.TextField(max_length=3000)
    conditions = models.TextField(max_length=3000, default="placeholder")
    circumstances = models.TextField(max_length=3000, default="placeholder")
    artifacts = models.TextField(max_length=3000, default="placeholder")
    modal_1 = models.TextField(max_length=3000)
    modal_2 = models.TextField(max_length=3000)
    modal_3 = models.TextField(max_length=3000)
    world_modal_1 = models.TextField(max_length=3000, default="placeholder")
    world_modal_2 = models.TextField(max_length=3000, default="placeholder")
    world_modal_3 = models.TextField(max_length=3000, default="placeholder")
    encumbrance = models.TextField(max_length=3000, default="placeholder")
    dodge_roll = models.ForeignKey(Roll, on_delete=models.CASCADE, blank=True, null=True,
                                   related_name="char_dodge")
    sprint_roll = models.ForeignKey(Roll, on_delete=models.CASCADE, blank=True, null=True,
                                    related_name="char_sprint")

class AttributeBonus(models.Model):
    character = models.ForeignKey('Character', on_delete=models.CASCADE)
    attribute = models.ForeignKey('Attribute', on_delete=models.CASCADE)
    value = models.PositiveIntegerField()

    class Meta:
        unique_together = (("character", "attribute"))
        indexes = [
            models.Index(fields=['character', 'attribute']),
        ]

