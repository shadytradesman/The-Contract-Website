import math

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.datetime_safe import datetime
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm

from hgapp.utilities import get_queryset_size
from cells.models import Cell
from characters.signals import GrantAssetGift, VoidAssetGifts

import random
import hashlib

HIGH_ROLLER_STATUS = (
    ('ANY', 'Any'),
    ('NEWBIE', 'Newbie'),
    ('NOVICE', 'Novice'),
    ('SEASONED', 'Seasoned'),
    ('VETERAN', 'Veteran'),
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

BODY_STATUS = (
    'Bruised',
    'Bruised',
    'Hurt',
    'Injured',
    'Wounded',
    'Mauled',
    'Maimed'
)

MIND_STATUS = (
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

EQUIPMENT_DEFAULT = """
#### On Person

* Clothes
* Wallet
* Keys
* flask of tears
* Rugged no-metal belt that can be used as a pair of nunchucks

#### In Bag

* Oxygen canister
* Census-taker's liver
* Fava Beans
* Chianti
"""

# EXPERIENCE CONSTANTS
# These can be changed at will as the historical values are all dynamically calculated.
EXP_MVP = 2
EXP_LOSS = 2
EXP_WIN = 4
EXP_GM = 4
EXP_NEW_CHAR = 150
EXP_COST_QUIRK_MULTIPLIER = 3
EXP_ADV_COST_ATTR_MULTIPLIER = 4
EXP_ADV_COST_SKILL_MULTIPLIER = 2
EXP_ADV_COST_SOURCE_MULTIPLIER = 2
EXP_COST_SKILL_INITIAL = 2
EXP_COST_TRAUMA_THERAPY = 3

# STAT CONSTANTS
BASE_MIND_LEVELS = 5
BASE_BODY_LEVELS = 5



def random_string():
    return hashlib.sha224(bytes(random.randint(1, 99999999))).hexdigest()

class Character(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200)
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
            total = total + power.get_point_value()
        return total

    def number_of_victories(self):
        return get_queryset_size(self.game_attendance_set.exclude(is_confirmed=False).filter(outcome="WIN"))

    def number_of_losses(self):
        return get_queryset_size(self.game_attendance_set.exclude(is_confirmed=False).filter(outcome="LOSS"))

    def calculate_status(self):
        num_victories = self.number_of_victories()
        if num_victories == 0 and self.number_of_losses() == 0:
            return HIGH_ROLLER_STATUS[1][0]
        elif num_victories < 10:
            return HIGH_ROLLER_STATUS[2][0]
        elif num_victories < 30:
            return HIGH_ROLLER_STATUS[3][0]
        else:
            return HIGH_ROLLER_STATUS[4][0]

    def save(self, *args, **kwargs):
        self.status = self.calculate_status()
        if self.pk is None:
            super(Character, self).save(*args, **kwargs)
            self.set_default_permissions()
        else:
            self.set_default_permissions()
            super(Character, self).save(*args, **kwargs)

    def delete(self):
        self.is_deleted=True
        self.save()

    def player_has_cell_edit_perms(self, player):
        if self.cell:
            return self.cell.player_can_edit_characters(player)
        else:
            return False

    def player_can_edit(self, player):
        if not hasattr(self, 'player') or not self.player:
            return False
        if self.is_deleted:
            return False
        can_edit = player.has_perm('edit_character', self) or self.player_has_cell_edit_perms(player)
        can_view_private = self.player_can_view(player)
        return can_edit and can_view_private

    def player_can_view(self, player):
        if not hasattr(self, 'player') or not self.player:
            return True
        if self.is_deleted:
            return False
        return not self.private or player.has_perm("view_private_character", self) or self.player_has_cell_edit_perms(player)

    def completed_games(self):
        return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("relevant_game__end_time").all()

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
        return len(self.character_death_set.filter(is_void=False).all()) > 0

    def real_death(self):
        non_void_deaths = self.character_death_set.filter(is_void=False).all()
        if len(non_void_deaths) > 0:
            return non_void_deaths[0]
        else:
            return None

    def void_deaths(self):
        return self.character_death_set.filter(is_void=True).all()

    def delete_upcoming_attendances(self):
        scheduled_game_attendances = self.scheduled_game_attendances()
        for game_attendance in scheduled_game_attendances:
            game_attendance.delete()

    def active_game_attendances(self):
        return [game for game in self.game_attendance_set.all() if game.relevant_game.is_active()]

    def scheduled_game_attendances(self):
        return [game for game in self.game_attendance_set.all() if game.relevant_game.is_scheduled()]

    def active_spent_rewards(self):
        return self.reward_set.filter(is_void=False).exclude(relevant_power=None).all()

    def active_rewards(self):
        return self.reward_set.filter(is_void=False).all()

    def spent_rewards(self):
        return self.reward_set.exclude(relevant_power=None).order_by("assigned_on", "awarded_on").all()

    def unspent_rewards(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).order_by("is_improvement", "-awarded_on").all()

    def unspent_gifts(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).filter(is_improvement=False).order_by("-awarded_on").all()

    def unspent_improvements(self):
        return self.reward_set.filter(is_void=False).filter(relevant_power=None).filter(is_improvement=True).order_by("-awarded_on").all()

    def reward_cost_for_power(self, power_full):
        rewards_to_be_spent = []
        unspent_gifts = self.unspent_gifts()
        unspent_improvements = self.unspent_improvements()
        num_improvements_to_spend = 0
        if len(unspent_gifts) > 0:
            rewards_to_be_spent.append(unspent_gifts[0])
        for a in range(power_full.get_point_value() - 1):
            if len(unspent_improvements) > a:
                num_improvements_to_spend += 1
                rewards_to_be_spent.append(unspent_improvements[a])
            elif (len(unspent_gifts) > 0) and (len(unspent_gifts) > (a - num_improvements_to_spend + 1)):
                rewards_to_be_spent.append(unspent_gifts[(a - num_improvements_to_spend + 1)])
            else:
                break
        return rewards_to_be_spent

    def improvement_ok(self):
        return self.number_of_victories() * 2 >  len(self.active_rewards())

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
                               self.get_status_display(),
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
        rewards = self.experiencereward_set.all()
        total_exp = EXP_NEW_CHAR
        for reward in rewards:
            total_exp = total_exp + reward.get_value()
        return int(total_exp)

    def exp_cost(self):
        return self.stats_snapshot.exp_cost

    # WARNING: this is an expensive call
    def regen_stats_snapshot(self):
        stat_diffs = self.contractstats_set.filter(is_snapshot=False).order_by("created_time").all()
        asset_details = []
        liability_details = []
        ability_values = []
        attribute_values = []
        limit_revisions = []
        trauma_revisions = []
        source_revisions = []
        cost = 0
        for diff in stat_diffs:
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
        brawn_value = self.stats_snapshot.attributevalue_set.get(relevant_attribute__scales_body=True).value
        return BASE_BODY_LEVELS + math.ceil(brawn_value / 2)

    def num_mind_levels(self):
        intelligence_value = self.stats_snapshot.attributevalue_set.get(relevant_attribute__scales_mind=True).value
        return BASE_MIND_LEVELS + math.ceil(intelligence_value / 2)

    def get_attributes(self, is_physical):
        return self.stats_snapshot.attributevalue_set\
            .filter(relevant_attribute__is_physical=is_physical)\
            .order_by('relevant_attribute__name')\
            .all()

    def get_abilities(self, is_physical):
        return self.stats_snapshot.abilityvalue_set\
            .filter(relevant_ability__is_physical=is_physical)\
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

class BattleScar(models.Model):
    character = models.ForeignKey(Character,
                                   on_delete=models.CASCADE)
    description = models.CharField(max_length=500)

class Injury(models.Model):
    character = models.ForeignKey(Character,
                                   on_delete=models.CASCADE)
    description = models.CharField(max_length=500)
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

    # returns one of several potential classes. Intended to be used with visitor pattern
    def get_source(self):
        if hasattr(self, 'game_attendance'):
            return self.game_attendance
        if hasattr(self, 'game'):
            return self.game
        raise ValueError("Experience reward has no source")

    def source_blurb(self):
        if hasattr(self, 'game_attendance'):
            return "from attending " + self.game_attendance.relevant_game.scenario.title
        elif hasattr(self, 'game'):
            return "from GMing " + self.game.scenario.title
        else:
            raise ValueError("Experience reward has no source")

    def get_value(self):
        if hasattr(self, 'game_attendance'):
            attendance = self.game_attendance
            value = 0
            # if attendance.is_mvp():
            #     value = value + EXP_MVP
            if attendance.is_victory():
                value = value + EXP_WIN
            elif attendance.is_ringer_victory():
                value = value + EXP_WIN
            else:
                value = value + EXP_LOSS
            return value
        if hasattr(self, 'game'):
            return EXP_GM
        raise ValueError("Experience reward has no source")

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

class Attribute(Trait):
    scales_body = models.BooleanField(default=False)
    scales_mind = models.BooleanField(default=False)

class Ability(Trait):
    is_primary = models.BooleanField(default=False)

class Quirk(models.Model):
    name = models.CharField(max_length=150)
    value = models.PositiveIntegerField()
    description = models.CharField(max_length=2000)
    system = models.CharField(max_length=2000) # A "just the facts" summary
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
        super(QuirkDetails, self).save(*args, **kwargs)
        if self.previous_revision and self.is_deleted and self.relevant_asset.grants_gift:
            if not self.previous_revision.relevant_stats.is_snapshot:
                VoidAssetGifts.send_robust(sender=self.__class__,
                                      assetDetail=self,
                                      character=self.relevant_stats.assigned_character)
        if not self.previous_revision and not self.is_deleted and self.relevant_asset.grants_gift:
            if not self.relevant_stats.is_snapshot:
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

    def save(self, *args, **kwargs):
        if self.previous_revision:
            if self.previous_revision.relevant_stats.is_snapshot:
                raise ValueError("A Trait's parent revision cannot be owned by a snapshot.")
        super(TraitValue, self).save(*args, **kwargs)

class AttributeValue(TraitValue):
    relevant_attribute = models.ForeignKey(Attribute,
                                       on_delete=models.CASCADE)
    class Meta:
        unique_together = (("relevant_attribute", "relevant_stats"))
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

class AbilityValue(TraitValue):
    relevant_ability = models.ForeignKey(Ability,
                                       on_delete=models.CASCADE)
    class Meta:
        unique_together = (("relevant_ability", "relevant_stats"))
        indexes = [
            models.Index(fields=['relevant_stats']),
        ]

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
    def save(self, *args, **kwargs):
        if self.pk is None:
            self.relevant_character.delete_upcoming_attendances()
        super(Character_Death, self).save(*args, **kwargs)

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
    modal_1 = models.TextField(max_length=3000)
    modal_2 = models.TextField(max_length=3000)
    modal_3 = models.TextField(max_length=3000)