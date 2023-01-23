import math

import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Sum
from django.utils.datetime_safe import datetime
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db import transaction
from django.utils.dateparse import parse_datetime

from markdown_deux.templatetags.markdown_deux_tags import markdown_filter

from heapq import merge

from hgapp.utilities import get_queryset_size, get_object_or_none
from cells.models import Cell
from characters.signals import GrantAssetGift, VoidAssetGifts, AlterPortedRewards, transfer_consumables

import random
import hashlib


logger = logging.getLogger("app." + __name__)

STATUS_ANY = 'ANY'
STATUS_NEWBIE = 'NEWBIE'
STATUS_NOVICE = 'NOVICE'
STATUS_SEASONED = 'SEASONED'
STATUS_VETERAN = 'VETERAN'
HIGH_ROLLER_STATUS = (
    (STATUS_ANY, 'Any'),
    (STATUS_NEWBIE, 'Newbie'),
    (STATUS_NOVICE, 'Novice'),
    (STATUS_SEASONED, 'Seasoned'),
    (STATUS_VETERAN, 'Veteran'),
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

QUIRK_PHYSICAL = 'PHYSICAL'
QUIRK_BACKGROUND = 'BACKGROUND'
QUIRK_MENTAL = 'MENTAL'
QUIRK_RESTRICTED = 'RESTRICTED'
QUIRK_CATEGORY = (
    (QUIRK_PHYSICAL, 'Physical'),
    (QUIRK_BACKGROUND, 'Background'),
    (QUIRK_MENTAL, 'Mental'),
    (QUIRK_RESTRICTED, 'Restricted'),
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
START_ONLY_SCAR = "5STARTONLY"
SCAR_SEVERITY = (
    (MINOR_SCAR, "Minor Scars (Severity 4)"),
    (MAJOR_SCAR, "Major Scars (Severity 5)"),
    (SEVERE_SCAR, "Severe Scars (Severity 6)"),
    (EXTREME_SCAR, "Extreme Scars (Severity 7+)"),
    (START_ONLY_SCAR, "Asset and Liability Scars"),
)

THREAT_DANGEROUS = "1DANGEROUS"
THREAT_DEADLY = "3DEADLY"
THREAT_FATEFUL = "5FATEFUL"
LOOSE_END_THREAT = (
    (THREAT_DANGEROUS, "Dangerous"),
    (THREAT_DEADLY, "Deadly"),
    (THREAT_FATEFUL, "Fateful"),
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
WEAPON_THROWN_DISPLAY = "Thrown"
WEAPON_THROWN_OTHER = "THROWN_2" # doesn't show up on special thrown weapon gift
WEAPON_PROJECTILE = "PROJECTILE" # bows, slingshots, crossbows
WEAPON_OTHER = "OTHER" # Stun guns, caltrops, etc.
WEAPON_TYPE = (
    (WEAPON_MELEE, "Melee"),
    (WEAPON_UNARMED, "Unarmed"),
    (WEAPON_FIREARM, "Firearm"),
    (WEAPON_THROWN, WEAPON_THROWN_DISPLAY),
    (WEAPON_THROWN_OTHER,"Thrown other"),
    (WEAPON_PROJECTILE, "Projectile"),
    (WEAPON_OTHER, "Other")
)

CONDITION = "Condition"
CIRCUMSTANCE = "Circumstance"
TROPHY = "Trophy"
TRAUMA = "Trauma"
BATTLE_SCAR = "Battle Scar"
LOOSE_END = "Loose End"
ELEMENT_TYPE = (
    (CONDITION, 'Condition'),
    (CIRCUMSTANCE, 'Circumstance'),
    (TROPHY, 'Trophy'),
    (TRAUMA, 'Trauma'),
    (LOOSE_END, 'Loose End'),
)

ELEMENT_TYPE_INC_SCAR = (
    (CONDITION, 'Condition'),
    (CIRCUMSTANCE, 'Circumstance'),
    (TROPHY, 'Trophy'),
    (TRAUMA, 'Trauma'),
    (BATTLE_SCAR, 'Battle Scar'),
    (LOOSE_END, 'Loose End'),
)

GIVEN = "GIVEN"
STOLEN = "STOLEN"
LOOTED = "LOOTED"
ARTIFACT_TRANSFER_TYPE = (
    (GIVEN, 'given to'),
    (STOLEN, 'stolen by'),
    (LOOTED, 'looted by'),
)

LOST = "LOST"
DESTROYED = "DESTROYED"
RECOVERED = "RECOVERED"
REPAIRED = "REPAIRED"
AT_HOME = "ATHOME"
ARTIFACT_STATUS_CHANGE_TYPE = (
    (LOST, 'Lost'),
    (RECOVERED, 'Recovered'),
    (DESTROYED, "Destroyed"),
    (REPAIRED, "Repaired"),
    (AT_HOME, "At home")
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
EXP_GM_RATIO = "GM_GOLDEN_RATIO"
EXP_GM_NEW_PLAYER = "GM_NEW_PLAYER"
EXP_GM_MOVE = "GM_MOVE"
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
    (EXP_GM_RATIO, "GMing and achieving the Golden Ratio"),
    (EXP_GM_NEW_PLAYER, "GMing for a new Player"),
    (EXP_GM_MOVE, "GMing a Move"),
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
    EXP_GM_RATIO: 6,
    EXP_GM_NEW_PLAYER: 6,
    EXP_GM_MOVE: 2,
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
    return hashlib.sha224(bytes(random.randint(1, 999999))).hexdigest()


class Character(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, blank=True)
    player = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              null=True)
    edit_secret_key = models.CharField(default=random_string,
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
    is_dead = models.BooleanField(default=False)
    pub_date = models.DateTimeField('date published')
    edit_date = models.DateTimeField('date last edited')

    num_games = models.IntegerField(default=0)
    num_victories = models.IntegerField(default=0)
    num_losses = models.IntegerField(default=0)
    num_journals = models.IntegerField(default=0)

    ported = models.CharField(choices=PORT_STATUS,
                               max_length=50,
                               default=NOT_PORTED)

    # true if contractor has ever had a crafting gift. Shows crafting button.
    crafting_avail = models.BooleanField(default=False)
    # true when crafting button should be highlighted on sheet.
    highlight_crafting = models.BooleanField(default=False)

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
            models.Index(fields=['player', 'cell']),
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
            total = total + max(1, power.get_gift_cost())
        return total

    def world_element_cell_choices(self):
        if not hasattr(self, "player") or not self.player:
            return Cell.objects.none()
        queryset = self.player.cell_set.filter(cellmembership__is_banned=False).all()
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

    def player_can_gm(self, player):
        if player.is_superuser:
            return True
        if player.is_anonymous:
            return False
        if self.is_deleted:
            return False
        if not hasattr(self, 'player') or not self.player:
            return False
        if self.player == player:
            return False
        if not hasattr(self, 'cell') or not self.cell:
            return False
        return self.cell.player_can_run_games(player)

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
        return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("-relevant_game__end_time").first()

    def get_scenario_attendance(self, scenario):
        return self.game_attendance_set.filter(relevant_game__scenario=scenario).first()

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

    def real_death(self):
        return self.character_death_set.filter(is_void=False).first()

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

    def spent_rewards_rev_sort(self):
        return self.reward_set.exclude(relevant_power=None).order_by("-assigned_on").all()

    def rewards_spent_since_date(self, date):
        return self.reward_set.exclude(relevant_power=None, assigned_on__isnull=True).filter(assigned_on__gt=date)

    def spent_rewards(self):
        return self.reward_set.exclude(relevant_power=None).order_by("assigned_on", "awarded_on").all()

    def num_spent_rewards(self):
        return self.reward_set.exclude(relevant_power=None).count()

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

    def num_improvements(self):
        return self.reward_set.filter(is_void=False).filter(is_improvement=True).count()

    def reward_cost_for_item(self, sig_item):
        unspent_gifts = self.unspent_gifts()
        num_unspent_gifts = self.num_unspent_gifts()
        unspent_improvements = self.unspent_improvements()
        gifts_to_spend = []
        improvements_to_spend = []

        gifts_required = sig_item.power_full_set.count()
        gifts_to_spend.extend(unspent_gifts[0:gifts_required])

        improvements_required = - gifts_required
        for power in sig_item.power_full_set.all():
            improvements_required += power.get_gift_cost()
        improvements_to_spend.extend(unspent_improvements[0:max(improvements_required, 0)])

        num_needed_improvements = improvements_required - len(improvements_to_spend)
        if num_needed_improvements > 0:
            if len(gifts_to_spend) < num_unspent_gifts:
                gifts_to_spend.extend(unspent_gifts[gifts_required:num_needed_improvements])
        return {
            "rewards_to_spend": gifts_to_spend + improvements_to_spend,
            "gift_deficit": gifts_required - len(gifts_to_spend),
            "improvement_deficit": (improvements_required + gifts_required) - (len(gifts_to_spend) + len(improvements_to_spend)),
            "item_cost": improvements_required + gifts_required,
        }


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
        return self.number_of_victories() * 2 >= (self.active_rewards().count() - ported_adjustment)

    def get_powers_for_render(self):
        return self.power_full_set.all()

    def get_signature_items(self):
        return self.artifact_set.filter(cell=None, is_signature=True).all()

    def get_signature_items_crafted(self):
        return self.creator.filter(cell=None, is_signature=True).all()

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
        if self.character_death_set.filter(is_void=False).exists():
            raise ValueError("cannot kill a dead character")
        new_death = Character_Death(relevant_character=self,
                                    date_of_death=timezone.now())
        new_death.save()
        self.is_dead = True
        self.save()

    def source_name_values(self):
        values = []
        for rev in self.stats_snapshot.sourcerevision_set.all():
            source = rev.relevant_source
            values.append((source.name, (source.current_val, rev.max)),)
        return values

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

    def _archive_text_header(self):
        header_format = \
"""# {}

Played by: {}
Archived on: {}
{} Contractor with {} victories and {} losses

**{} is a {} who will risk {} life to {}.**
{} is {} years old, and often appears as {}.
{} 
        """
        if self.cell:
            location_blurb = "{} lives in {}, a setting {}.".format(self.name, self.cell.name,
                                                                    self.cell.setting_sheet_blurb)
        else:
            location_blurb = ""

        formatted_header = header_format.format(
            self.name,
            self.player.username if self.player else "an anonymous user",
            datetime.today(),
            self.get_contractor_status_display(),
            self.number_of_victories(),
            self.number_of_losses(),
            self.name,
            self.concept_summary,
            self.get_pronoun_display(),
            self.ambition,
            self.pres_tense_to_be(),
            self.age,
            self.appearance,
            location_blurb
        )
        return formatted_header

    def _archive_text_gifts(self):
        gift_texts = [power_full.latest_archive_text() for power_full in self.power_full_set.all()]
        return "#Gifts\n{}".format("\n".join(gift_texts))

    def _archive_text_other_stat_info(self):
        format_text = \
"""
## Body: {}

### Injuries 

{}

### Battle Scars

{}

## Mind: {}

### Limits

{}

### Traumas

{}
"""
        return format_text.format(self.num_body_levels(),
                                  "\n".join(
                                      ["* **{}** - {}".format(inj.severity, inj.description) for inj in self.injury_set.all()]
                                  ),
                                  "\n".join(
                                      ["* **{}** *({})*".format(scr.description, scr.system) for scr in self.battlescar_set.all()]
                                  ),
                                  self.num_mind_levels(),
                                  "\n".join(
                                      ["* **{}** *({})*".format(lim.relevant_limit.name, lim.relevant_limit.description) for lim in self.stats_snapshot.limitrevision_set.all()]
                                  ),
                                  "\n".join(
                                      ["* {}".format(trm.relevant_trauma.description) for trm in self.stats_snapshot.traumarevision_set.all()]
                                  ))

    def archive_txt(self):
        header = self._archive_text_header()
        stats = self.stats_snapshot.archive_text()
        other_stat_info = self._archive_text_other_stat_info()
        gifts = self._archive_text_gifts()
        return "\n\n".join([header, stats, other_stat_info, gifts])


    def can_get_bonus_exp(self):
        return not self.is_dead and self.exp_earned() < (EXP_NEW_CHAR + 10 + (self.num_victories * 12))


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
        crafting_cost = self.craftingevent_set.aggregate(Sum('total_exp_spent'))['total_exp_spent__sum']
        return self.stats_snapshot.exp_cost + crafting_cost if crafting_cost else self.stats_snapshot.exp_cost

    def ability_maximum(self):
        if self.status == HIGH_ROLLER_STATUS[3][0] or self.status == HIGH_ROLLER_STATUS[4][0] or self.ported != NOT_PORTED:
            return 6
        else:
            return 5

    def progress_loose_ends(self, game_start_time):
        loose_ends = self.looseend_set.filter(is_deleted=False, created_time__lte=game_start_time, cutoff__gte=1).all()
        for loose_end in loose_ends:
            if loose_end.cutoff > 0:
                loose_end.cutoff = loose_end.cutoff - 1
                loose_end.save()

    def has_due_loose_end(self):
        return self.looseend_set.filter(is_deleted=False, cutoff=0).count() > 0

    def to_create_power_blob(self):
        unspent_gifts = []
        unspent_improvements = []
        for reward in self.unspent_rewards().all():
            if reward.is_improvement:
                unspent_improvements.append("{} from {}".format(reward.type_text(), reward.reason_text()))
            else:
                unspent_gifts.append("{} from {}".format(reward.type_text(), reward.reason_text()))
        unspent_gifts.extend(unspent_improvements)
        return {
            "name": self.name,
            "avail_rewards": unspent_gifts,
            "status": self.status,
        }

    def get_abilities_by_name_and_id(self):
        char_ability_values = self.get_abilities()
        ability_value_by_id = {}
        char_value_ids = [x.relevant_ability.id for x in char_ability_values]
        primary_zero_values = [(x.name, x, 0) for x in Ability.objects.filter(is_primary=True).order_by("name").all()
                               if x.id not in char_value_ids]
        all_ability_values = []
        for x in char_ability_values:
            all_ability_values.append((x.relevant_ability.name, x.relevant_ability, x.value))
            ability_value_by_id[x.relevant_ability.id] = x.value
        return (list(merge(primary_zero_values, all_ability_values)), ability_value_by_id)

    def to_print_blob(self):
        abilities = self.get_abilities_by_name_and_id()[0]
        abilities = [(x[0], x[2]) for x in abilities]

        return {
            "name": self.name,
            "tagline": self.tagline,
            "player": self.player.username if self.player else "",
            "status": self.get_status_display(),
            "appearance": self.appearance,
            "sex": self.sex,
            "concept_summary": self.concept_summary,
            "ambition": self.ambition,
            "pronoun": self.get_pronoun_display(),
            "pronoun_pres": self.pres_tense_to_be(),
            "age": self.age,
            "num_games": self.num_games,
            "num_victories": self.num_victories,
            "num_losses": self.num_losses,
            "equipment": markdown_filter(self.equipment),
            "bio": markdown_filter(self.background),

            "mind": self.num_mind_levels(),
            "body": self.num_body_levels(),
            "source": self.source_name_values(),

            "attributes": [(x.relevant_attribute.name, x.value + self.get_bonus_for_attribute(x.relevant_attribute)) for x in self.get_attributes()],
            "abilities": abilities,
            "battle_scars": [(scr.description, scr.system) for scr in self.battlescar_set.all()],
            "limits": [(lim.relevant_limit.name, lim.relevant_limit.description) for lim in self.stats_snapshot.limitrevision_set.all()],
            "traumas": [(trm.relevant_trauma.name, trm.relevant_trauma.description) for trm in self.stats_snapshot.traumarevision_set.all()],
            "conditions": [(elem.name, elem.description, elem.system) for elem in self.condition_set.exclude(is_deleted=True).all()],
            "circumstances": [(elem.name, elem.description, elem.system) for elem in self.circumstance_set.exclude(is_deleted=True).all()],
            "trophies": [(elem.name, elem.description, elem.system) for elem in
                              self.artifact_set.filter(cell__isnull=False).exclude(is_deleted=True).all()],

            "loose_ends": [(end.name, end.description, end.get_cutoff_category(), end.get_threat_level_display(), end.system)
                           for end in self.looseend_set.filter(is_deleted=False).all()],

            "crafting_gifts": None,
            "artifacts": None,
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

    #TODO: Delete this after new powers update rollout
    def reset_attribute_bonuses(self):
        attributes = self.stats_snapshot.attributevalue_set.all()
        for attribute in attributes:
            self.set_bonus_for_attribute(attribute.relevant_attribute, 0)
        powers = self.power_full_set.all()
        bonus_by_attribute = {}
        for power in powers:
            if power.dice_system != 'PS2' or power.latest_revision().get_is_active():
                bonuses = power.latest_revision().get_attribute_bonuses()
                for attr, bonus in bonuses:
                    curr_bonus = bonus_by_attribute.get(attr, 0)
                    if bonus > curr_bonus:
                        bonus_by_attribute[attr] = bonus
        artifacts = self.artifact_set.filter(is_consumable=False, cell__isnull=True, is_deleted=False).all()
        for artifact in artifacts:
            artifact_powers = artifact.power_set.all()
            for power in artifact_powers:
                if power.get_is_active(artifact):
                    bonuses = power.get_attribute_bonuses()
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

    def __str__(self):
        return "[{}] {}".format(self.get_type_display(), self.description)


class BattleScar(models.Model):
    character = models.ForeignKey(Character,
                                   on_delete=models.CASCADE)
    description = models.CharField(max_length=5000)
    system = models.CharField(max_length=5000, blank=True)


class WorldElement(models.Model):
    # owning character
    # null for sig items without owners
    character = models.ForeignKey(Character, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=5000)
    description = models.CharField(max_length=5000)
    origin = models.CharField(max_length=2000, blank=True)
    system = models.CharField(max_length=5000, blank=True, help_text="Threat for Loose Ends")
    created_time = models.DateTimeField(auto_now_add=True, null=True) #null because added in migration
    is_deleted = models.BooleanField(default=False)
    # If true, this World Element was deleted by removing its related quirk.
    deleted_by_quirk_removal = models.BooleanField(default=True) # Default true to not mess up legacy sheets
    deleted_date = models.DateTimeField(null=True, blank=True)
    deletion_reason = models.CharField(max_length=5000, blank=True)
    granting_gm = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    # when cell is null, element is created by gift system
    cell = models.ForeignKey(Cell,
                             blank=True,
                             null=True,
                             on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

    # Return "Asset" or "Liability" if this world element was granted by one, otherwise return None
    def get_quirk_text(self):
        if self.assetdetails_set.first():
            return "Asset"
        if self.liabilitydetails_set.first():
            return "Liability"
        return None

    def mark_deleted(self, reason=None, deleted_by_quirk_removal=False):
        self.is_deleted = True
        self.deleted_by_quirk_removal = deleted_by_quirk_removal
        self.deleted_date = timezone.now()
        if reason:
            self.deletion_reason = reason
        self.save()

    def record_of_quirk_grant(self):
        return self.created_time > parse_datetime("2022-10-19 15:56:13.441822+00:00")


class Condition(WorldElement):

    def get_type_display(self):
        return "Condition"


class Circumstance(WorldElement):

    def get_type_display(self):
        return "Circumstance"


class LooseEnd(WorldElement):
    granting_player = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, related_name="granting_gm")
    cutoff = models.PositiveIntegerField(default=1)
    threat_level = models.CharField(choices=LOOSE_END_THREAT, max_length=45, default=THREAT_DANGEROUS)
    original_cutoff = models.PositiveIntegerField(default=1)
    # use self.system field for threat information
    how_to_tie_up = models.CharField(max_length=5000, blank=True)

    CUTOFF_NOW = "present"
    CUTOFF_IMMINENT = "imminent"
    CUTOFF_MODERATE = "moderate"
    CUTOFF_LONG = "distant"

    def get_type_display(self):
        return "Loose End"

    def is_loose_end(self):
        return True

    def get_threat_level_hover_text(self):
        if self.threat_level == THREAT_DANGEROUS:
            return "The sort of threat which may crop up for people in the real world. For example, The loss of " \
                   "resources or equipment, imprisonment, infamy,  or mundane gang-level violence."
        if self.threat_level == THREAT_DEADLY:
            return "A supernatural or extreme threat that poses a significant risk even to Contractors." \
                    "For example, An assassination attempt from a powerful foe or organization, being put into a coma, " \
                   "gaining a severe curse. "
        if self.threat_level == THREAT_FATEFUL:
            return "Reserved for Loose Ends which will cause certain or almost-certain death when the Cutoff hits 0. " \
                   "For example, A chronic deadly disease, an implanted bomb exploding, an assassination attempt from a harbinger-level foe."

    def get_cutoff_category(self):
        if self.cutoff == 0:
            return LooseEnd.CUTOFF_NOW
        if self.cutoff < 3:
            return LooseEnd.CUTOFF_IMMINENT
        if self.cutoff < 5:
            return LooseEnd.CUTOFF_MODERATE
        return LooseEnd.CUTOFF_LONG


class StockElementCategory(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class StockWorldElement(models.Model):
    name = models.CharField(max_length=500)
    description = models.CharField(max_length=5000)
    system = models.CharField(max_length=1000, blank=True, help_text="Threat for Loose Ends")
    type = models.CharField(choices=ELEMENT_TYPE,
                            max_length=45,
                            default=CONDITION)
    category = models.ForeignKey(StockElementCategory, on_delete=models.CASCADE)
    cutoff = models.PositiveIntegerField("cutoff (for loose ends)", default=1)
    how_to_tie_up = models.CharField(max_length=1000, blank=True, help_text="For Loose Ends only")
    threat_level = models.CharField(choices=LOOSE_END_THREAT, max_length=45, default=THREAT_DANGEROUS, help_text="for loose ends only")
    is_user_created = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['is_user_created']),
        ]

    def __str__(self):
        return "[{}] {} - {}".format(self.get_type_display(), self.category.name, self.name)

    def count_words(self):
        return len(self.name.split(" ")) + \
               len(self.description.split(" ")) + \
               len(self.system.split(" ")) + \
               len(self.how_to_tie_up.split(" "))


    def grant_to_character(self, stats, name_override=None):
        name = name_override if name_override is not None else self.name
        if self.type in [CONDITION, CIRCUMSTANCE, TROPHY]:
            ElementClass = Condition if self.type == CONDITION else Artifact if self.type == TROPHY else Circumstance
            return ElementClass.objects.create(character=stats.assigned_character,
                             name=name,
                             description=self.description,
                             system=self.system,)
        if self.type == TRAUMA:
            new_trauma = Trauma.objects.create(name=name, description=self.description)
            TraumaRevision.objects.create(relevant_stats=stats, relevant_trauma=new_trauma)
            return
        if self.type == LOOSE_END:
            return LooseEnd.objects.create(
                character=stats.assigned_character,
                name=name,
                description=self.description,
                system=self.system,
                cutoff=self.cutoff,
                threat_level=self.threat_level,
                how_to_tie_up=self.how_to_tie_up,
                granting_gm=stats.assigned_character.player)
        raise ValueError("Could not grant element to contractor")

    def grant_to_character_no_trauma(self, character, granting_player, cell):
        name = self.name
        if self.type in [CONDITION, CIRCUMSTANCE, TROPHY]:
            ElementClass = Condition if self.type == CONDITION else Artifact if self.type == TROPHY else Circumstance
            return ElementClass.objects.create(character=character,
                                               name=name,
                                               cell=cell,
                                               description=self.description,
                                               system=self.system,)
        if self.type == TRAUMA:
            raise ValueError("Cannot grant a trauma without specifying stats revision")
        if self.type == LOOSE_END:
            return LooseEnd.objects.create(
                character=character,
                name=name,
                cell=cell,
                description=self.description,
                system=self.system,
                cutoff=self.cutoff,
                threat_level=self.threat_level,
                how_to_tie_up=self.how_to_tie_up,
                granting_gm=granting_player)
        raise ValueError("Could not grant element to contractor")


class Artifact(WorldElement):
    # Signature Items creator
    crafting_character = models.ForeignKey(Character, related_name="creator", on_delete=models.CASCADE, null=True)
    creating_player = models.ForeignKey(settings.AUTH_USER_MODEL,
                                        on_delete=models.CASCADE,
                                        null=True,
                                        related_name = "creating_player")
    is_consumable = models.BooleanField(default=False)
    is_signature = models.BooleanField(default=False)
    is_crafted_artifact = models.BooleanField(default=False)
    since_revised = models.BooleanField(default=False) # gift has seen major revision since crafting.
    quantity = models.PositiveIntegerField(default=1)
    location = models.CharField(max_length=1000, default="", blank=True)
    most_recent_status_change = models.CharField(choices=ARTIFACT_STATUS_CHANGE_TYPE, max_length=55, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['crafting_character']),
            models.Index(fields=['creating_player']),
            models.Index(fields=['character']),
        ]

    def after_use_quantity(self):
        return self.quantity - 1

    def get_assigned_rewards(self):
        rewards = []
        for power in self.power_full_set.all():
            rewards.extend(power.reward_list())
        return rewards

    def get_latest_transfer(self):
        return self.artifacttransferevent_set.order_by("-created_time").first()

    def get_all_transfers(self):
        return self.artifact_.order_by("-created_time").all()

    def change_availability(self, status_type, notes=""):
        if status_type == self.most_recent_status_change:
            raise ValueError("Cannot change status type to current type")
        if not self.most_recent_status_change or self.most_recent_status_change in [RECOVERED, REPAIRED]:
            if status_type in [RECOVERED, REPAIRED]:
                raise ValueError("Cannot recover / repair an available artifact.")
        self.most_recent_status_change = status_type
        ArtifactStatusChange.objects.create(
            relevant_artifact=self,
            notes=notes,
            status_change_type=status_type)
        self.save()

    def transfer_to_character(self, transfer_type, to_character, notes="", quantity=1):
        if self.cell:
            raise ValueError("Cannot transfer non-gift artifacts")
        if self.is_deleted:
            raise ValueError("Cannot transfer deleted artifact")
        if quantity > self.quantity:
            raise ValueError("Cannot transfer more than you have.")
        if quantity == 0:
            return
        if self.character == to_character:
            raise ValueError("Cannot transfer an artifact to the character that possesses it.")
        ArtifactTransferEvent.objects.create(
            from_character=self.character,
            to_character=to_character,
            relevant_artifact=self,
            notes=notes,
            transfer_type=transfer_type,
            quantity=quantity)
        if self.is_consumable:
            self.__transfer_consumables_to_character(transfer_type, to_character, notes, quantity)
        else:
            self.character = to_character
        self.save()

    def __transfer_consumables_to_character(self, transfer_type, to_character, notes, quantity):
        power = self.power_set.first()
        target_artifacts = to_character.artifact_set.filter(is_consumable=True, crafting_character=self.crafting_character, is_deleted=False).all()
        new_stack = None
        for art in target_artifacts:
            if art.power_set.first() == power:
                new_stack = art
                new_stack.quantity += quantity
                new_stack.save()
        if new_stack is None:
            new_stack = Artifact.objects.create(
                character=to_character,
                name=self.name,
                description=self.description,
                system=self.system,
                crafting_character=self.crafting_character,
                creating_player=self.creating_player,
                is_consumable=True,
                since_revised=self.since_revised,
                quantity=quantity
            )
        self.quantity -= quantity
        # create another transfer event for the new artifact stack.
        ArtifactTransferEvent.objects.create(
            from_character=self.character,
            to_character=to_character,
            relevant_artifact=new_stack,
            notes=notes,
            transfer_type=transfer_type,
            quantity=quantity)
        transfer_consumables.send(sender=self.__class__,
                                         original_artifact=self,
                                         new_artifact=new_stack,
                                         quantity=quantity,
                                         power=power)


class ArtifactStatusChange(models.Model):
    relevant_artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=5000, blank=True)
    status_change_type = models.CharField(choices=ARTIFACT_STATUS_CHANGE_TYPE, max_length=55)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_artifact', 'created_time']),
        ]

    def get_timeline_string(self):
        time = self.created_time.strftime("%d %b %Y")
        line = "{} - <b>{}</b> ".format(time, self.get_status_change_type_display())
        if self.notes:
            line = line + '<i class="text-muted" style="padding-left: 5px;">({})</i>'.format(self.notes)
        return line



class ArtifactTransferEvent(models.Model):
    from_character = models.ForeignKey(Character, related_name="from_artifact_status", on_delete=models.CASCADE, null=True)
    to_character = models.ForeignKey(Character, related_name="to_artifact_status", on_delete=models.CASCADE, null=True)
    relevant_artifact = models.ForeignKey(Artifact, on_delete=models.CASCADE)
    created_time = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=5000, blank=True)
    transfer_type = models.CharField(choices=ARTIFACT_TRANSFER_TYPE, max_length=55)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_artifact', 'created_time']),
        ]

    def get_timeline_string(self):
        time = self.created_time.strftime("%d %b %Y")
        line = "{} - <b>{}</b> {} (from {})".format(time,
                                                    self.get_transfer_type_display(),
                                                    self.to_character.name if self.to_character else "nobody",
                                                    self.from_character.name if self.from_character else "nobody")
        if self.notes:
            line = line + '<i class="text-muted" style="padding-left: 5px;">({})</i>'.format(self.notes)
        return line


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

    def __str__(self):
        return "{} for {} ({})".format(self.get_value(), self.rewarded_player.username, self.type)

    def mark_void(self):
        self.is_void = True
        self.save()

    def source_blurb(self):
        if hasattr(self, 'custom_reason') and self.custom_reason:
            return mark_safe(self.custom_reason)
        reason = "from {}".format(self.get_type_display())
        if self.type == EXP_GM:
            return "{} {}".format(reason, self.game.scenario.title)
        if self.type in [EXP_GM_NEW_PLAYER, EXP_GM_RATIO]:
            return "{} in {}".format(reason, self.game.scenario.title)
        if self.type == EXP_GM_MOVE:
            return "{} in {}: {}".format(reason, self.move.cell, self.move.title)
        if self.type == EXP_JOURNAL:
            return mark_safe("<a href={}>{}: {}</a>".format(
                reverse("journals:journal_read_id", args=(self.journal.pk,)),
                reason,
                self.journal.title))
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

    def render_ps2_html_for_current_contractor(self):
        if self.parry_type != NO_PARRY_INFO:
            return self.get_defense_text_ps2()
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
                      "</span>" \
            .format(self.get_main_roll_component(),
                    self.attribute_id if hasattr(self, "attribute") and self.attribute else " ",
                    self.ability_id if hasattr(self, "ability") and self.ability else " ",
                    self.is_mind,
                    self.is_body)
        roll_text = mark_safe(html_output)
        return roll_text

    def render_value_for_ps2(self):
        if self.parry_type != NO_PARRY_INFO:
            return self.get_defense_text_ps2()
        first_word = "Mind" if self.is_mind else "Body" if self.is_body else self.attribute.name
        if self.ability:
            roll_text = "{} + {}".format(first_word, self.ability.name)
        else:
            roll_text = first_word
        return roll_text

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
                self.attribute_id if hasattr(self, "attribute") and self.attribute else " ",
                self.ability_id if hasattr(self, "ability") and self.ability else " ",
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

    def get_defense_text_ps2(self):
        if self.parry_type == DODGE_ONLY:
            roll_text = "to Dodge"
        else:
            roll_text = "to Dodge or Defend"
        if self.speed != NO_SPEED_INFO:
            roll_text = "{} as {}".format(roll_text, self.get_speed_display())
        return roll_text

    def get_defense_text(self):
        if self.parry_type == DODGE_ONLY:
            roll_text = "to dodge"
        else:
            roll_text = "to dodge or Defend (as for {})".format(self.get_parry_type_display())
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

    def get_type_cat(self):
        if self.type == WEAPON_THROWN_OTHER:
            return WEAPON_THROWN, WEAPON_THROWN_DISPLAY
        else:
            return self.type, self.get_type_display()

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
                              default=QUIRK_PHYSICAL)
    eratta = models.CharField(max_length=2500,
                              blank = True,
                              null = True)
    details_field_name = models.CharField(max_length=150,
                              blank = True,
                              null = True)
    multiplicity_allowed = models.BooleanField(default=False)
    grants_gift = models.BooleanField(default=False)
    grants_element = models.ForeignKey(StockWorldElement, on_delete=models.CASCADE, blank=True, null=True, help_text="Grants stock element")
    grants_scar = models.ForeignKey(StockBattleScar, on_delete=models.CASCADE, blank=True, null=True, help_text="Grants stock scar")
    grants_non_stock_element = models.CharField(
        choices=ELEMENT_TYPE_INC_SCAR,
        max_length=55,
        blank=True,
        help_text="Grants world element that isn't stock. Don't set if using one of the stock world elements.")

    class Meta:
        abstract = True

    def to_blob(self):
        # This method works similarly to what is displayed in the character creation page quirk_snippet.html
        blob = {
            "name": self.name,
            "category": self.get_category_display(),
            "value": self.value,
            "errata": self.eratta,
        }

        granted_element = self.grants_element
        if granted_element:
            blob["element_type"] = granted_element.get_type_display()
            blob["description"] = granted_element.description
            if granted_element.type == 'Loose End':
                blob["system"] = ""
            else:
                blob["system"] = granted_element.system
        elif self.grants_scar:
            granted_scar = self.grants_scar
            blob["element_type"] = "Battle Scar"
            blob["description"] = self.description
            blob["system"] = granted_scar.system
        else:
            blob["element_type"] = ""
            blob["description"] = self.description
            blob["system"] = self.system

        return blob

    def is_physical(self):
        return self.category == QUIRK_PHYSICAL

    def is_background(self):
        return self.category == QUIRK_BACKGROUND

    def is_mental(self):
        return self.category == QUIRK_MENTAL

    def is_restricted(self):
        return self.category == QUIRK_RESTRICTED

    def __str__(self):
        return self.name

    def grant_element_if_needed(self, stats, details=None):
        granted_element = self.grants_element
        if granted_element:
            name = "{}: {}".format(self.name, details) if details else self.name
            return granted_element.grant_to_character(stats, name)
        granted_scar = self.grants_scar
        if granted_scar:
            BattleScar.objects.create(character=stats.assigned_character,
                                      description=granted_scar.description,
                                      system=granted_scar.system)
        if self.grants_non_stock_element:
            elem_type = self.grants_non_stock_element
            if elem_type in [CONDITION, CIRCUMSTANCE, TROPHY]:
                ElementClass = Condition if elem_type == CONDITION else Artifact if elem_type == TROPHY else Circumstance
                return ElementClass.objects.create(character=stats.assigned_character,
                                            name=self.name,
                                            description=self.description,
                                            system=details, )
            elif elem_type == TRAUMA:
                new_trauma = Trauma.objects.create(name=self.name, description=details)
                TraumaRevision.objects.create(relevant_stats=stats, relevant_trauma=new_trauma)
            elif elem_type == BATTLE_SCAR:
                BattleScar.objects.create(character=stats.assigned_character,
                                          description=details,
                                          system="")
        return None


class Asset(Quirk):

    def is_liability(self):
        return False


class Liability(Quirk):

    def is_liability(self):
        return True


class Trauma(models.Model):
    name = models.CharField(max_length=5000, blank=True)
    description = models.CharField(max_length=5000)


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


    def archive_text(self):
        format_string = \
"""## Stats

### Attributes
{}

### Abilities
{}"""
        attribute_phrases = []
        for attribute in self.attributevalue_set.all():
            if attribute.relevant_attribute.is_deprecated or not attribute.previous_revision:
                continue
            attribute_phrases.append("**{}:** {}".format(attribute.relevant_attribute.name, attribute.value))
        attributes_txt = "\n".join(attribute_phrases)

        ability_phrases = []
        for ability in self.abilityvalue_set.all():
            ability_phrases.append("**{}:** {}".format(ability.relevant_ability.name, ability.value))
        abilities_txt = "\n".join(ability_phrases)

        return format_string.format(attributes_txt, abilities_txt)

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
            if attribute.relevant_attribute.is_deprecated or not attribute.previous_revision:
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
    relevant_condition = models.ForeignKey(Condition, null=True, blank=True, on_delete=models.CASCADE)
    relevant_circumstance = models.ForeignKey(Circumstance, null=True, blank=True, on_delete=models.CASCADE)
    relevant_loose_end = models.ForeignKey(LooseEnd, null=True, blank=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.previous_revision:
            if self.previous_revision.relevant_stats.is_snapshot:
                raise ValueError("A Quirk's parent revision cannot be owned by a snapshot.")
        super(QuirkDetails, self).save(*args, **kwargs)

    def relevant_element(self):
        if hasattr(self, "relevant_condition") and self.relevant_condition:
            return self.relevant_condition
        if hasattr(self, "relevant_circumstance") and self.relevant_circumstance:
            return self.relevant_circumstance
        if hasattr(self, "relevant_loose_end") and self.relevant_loose_end:
            return self.relevant_loose_end
        return None

    def grant_quirk_element(self):
        element = self.relevant_quirk().grant_element_if_needed(self.relevant_stats, self.details)
        if element:
            if isinstance(element, Condition):
                self.relevant_condition = element
            if isinstance(element, Circumstance):
                self.relevant_circumstance = element
            if isinstance(element, LooseEnd):
                self.relevant_loose_end = element
        super().save()


class AssetDetails(QuirkDetails):
    relevant_asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.previous_revision:
            elem = self.previous_revision.relevant_element()
            if self.is_deleted:
                if self.relevant_asset.grants_gift:
                    VoidAssetGifts.send_robust(sender=self.__class__,
                                               assetDetail=self,
                                               character=self.relevant_stats.assigned_character)
                if elem:
                    elem.mark_deleted("Asset refunded", True)
            elif self.details != self.previous_revision.details:
                elem.mark_deleted("Asset edited", True)
                self.grant_quirk_element()

        if not self.previous_revision and not self.is_deleted:
            if self.relevant_asset.grants_gift:
                GrantAssetGift.send_robust(sender=self.__class__,
                                      assetDetail=self,
                                      character=self.relevant_stats.assigned_character)
            self.grant_quirk_element()

    class Meta:
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

    def relevant_quirk(self):
        return self.relevant_asset


class LiabilityDetails(QuirkDetails):
    relevant_liability = models.ForeignKey(Liability, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.previous_revision and not self.is_deleted:
            self.grant_quirk_element()
        if self.previous_revision:
            elem = self.previous_revision.relevant_element()
            if elem:
                if self.is_deleted:
                    elem.mark_deleted("Liability bought off", True)
                elif self.details != self.previous_revision.details:
                    elem.mark_deleted("Liability edited", True)
                    self.grant_quirk_element()


    def relevant_quirk(self):
        return self.relevant_liability


class TraitValue(models.Model):
    relevant_stats = models.ForeignKey(ContractStats, on_delete=models.CASCADE)
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
    relevant_attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)

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
        char = self.relevant_character
        char.is_dead = char.character_death_set.filter(is_void=False).exists()
        char.save()


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
    loose_ends = models.TextField(max_length=3000, default="placeholder")
    moves = models.TextField(max_length=3000, default="placeholder")
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
    professions = models.JSONField(default=list)
    archetypes = models.JSONField(default=list)
    personality_traits = models.JSONField(default=list)
    paradigms = models.JSONField(default=list)
    ambitions = models.JSONField(default=list)


# TODO: Potentially delete this after new powers update rollout
class AttributeBonus(models.Model):
    character = models.ForeignKey('Character', on_delete=models.CASCADE)
    attribute = models.ForeignKey('Attribute', on_delete=models.CASCADE)
    value = models.PositiveIntegerField()

    class Meta:
        unique_together = (("character", "attribute"))
        indexes = [
            models.Index(fields=['character', 'attribute']),
        ]

