from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.datetime_safe import datetime
from django.utils import timezone
from guardian.shortcuts import assign_perm, remove_perm

from hgapp.utilities import get_queryset_size
from cells.models import Cell

HIGH_ROLLER_STATUS = (
    ('ANY', 'Any'),
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

class Character(models.Model):
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200)
    player = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE)
    status = models.CharField(choices=HIGH_ROLLER_STATUS,
                              max_length=25,
                              default=HIGH_ROLLER_STATUS[1][0])
    appearance = models.TextField(max_length=3000)
    age = models.CharField(max_length=50)
    sex = models.CharField(max_length=15)
    concept_summary = models.CharField(max_length=150)
    ambition = models.CharField(max_length=150)
    private = models.BooleanField(default=False)
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
                                blank=True)
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

    class Meta:
        permissions = (
            ('view_private_character', 'View private character'),
            ('edit_character', 'Edit character'),
        )

    def set_default_permissions(self):
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
        if num_victories < 10:
            return HIGH_ROLLER_STATUS[1][0]
        elif num_victories < 30:
            return HIGH_ROLLER_STATUS[2][0]
        else:
            return HIGH_ROLLER_STATUS[3][0]

    def save(self, *args, **kwargs):
        self.status = self.calculate_status()
        if self.pk is None:
            super(Character, self).save(*args, **kwargs)
            self.set_default_permissions()
        else:
            self.set_default_permissions()
            super(Character, self).save(*args, **kwargs)

    def player_has_cell_edit_perms(self, player):
        if self.cell:
            return self.cell.player_can_edit_characters(player)
        else:
            return False

    def player_can_edit(self, player):
        can_edit = player.has_perm('edit_character', self) or self.player_has_cell_edit_perms(player)
        can_view_private = self.player_can_view(player)
        return can_edit and can_view_private

    def player_can_view(self, player):
        return not self.private or player.has_perm("view_private_character", self) or self.player_has_cell_edit_perms(player)

    def completed_games(self):
        return self.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("relevant_game__end_time").all()

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
        return self.name + " [" + self.player.username + "]"

    def kill(self):
        if self.is_dead():
            raise ValueError("cannot kill a dead character")
        new_death = Character_Death(relevant_character=self,
                                    date_of_death=timezone.now())
        new_death.save()

    def archive_txt(self):
        output = "{}\nPlayed by: {}\nArchived on {}\n{} with {} wins and {} losses\n"
        output = output.format(self.name, self.player.username, datetime.today(), self.get_status_display(), self.number_of_victories(), self.number_of_losses())
        output = output + "Age: {}\nSex: {}\nAppearance: {}\nConcept: {}\nAmbition: {}\n"
        output = output.format(self.age, self.sex, self.appearance, self.concept_summary, self.ambition)
        output = output + "Stats: {}\n"
        output = output.format(self.basic_stats.stats)
        output = output + "\n=======\nPowers:\n=======\n"
        for power_full in self.power_full_set.all():
            output = output +"{}\n"
            output = output.format(power_full.latest_archive_txt())
        return output


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

## ADVANCED STATS

class Trait(models.Model):
    name = models.CharField(max_length=50)
    tutorialText = models.CharField(max_length=250,
                              null=True,
                              blank=True)
    def __str__(self):
        return self.name

    class Meta:
        abstract = True

class Attribute(Trait):
    pass

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


class Limit(models.Model):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=1000)
    is_default = models.BooleanField(default=False)

class ContractStats(models.Model):
    attributes = models.ManyToManyField(Attribute,
                                       blank=True,
                                       through="AttributeValue",
                                       through_fields=('relevant_stats', 'relevant_attribute'))
    abilities = models.ManyToManyField(Ability,
                                       blank=True,
                                       through="AbilityValue",
                                       through_fields=('relevant_stats', 'relevant_ability'))
    assets = models.ManyToManyField(Asset,
                                   blank=True,
                                   through="AssetDetails",
                                   through_fields=('relevant_stats', 'relevant_asset'))
    liabilities = models.ManyToManyField(Liability,
                                   blank=True,
                                   through="LiabilityDetails",
                                   through_fields=('relevant_stats', 'relevant_liability'))
    limits = models.ManyToManyField(Limit,
                                    blank=True)


class QuirkDetails(models.Model):
    relevant_stats = models.ForeignKey(ContractStats,
                                       on_delete=models.CASCADE)
    details = models.CharField(max_length=2000)

    class Meta:
        abstract = True

class AssetDetails(QuirkDetails):
    relevant_asset = models.ForeignKey(Asset,
                                       on_delete=models.CASCADE)

class LiabilityDetails(QuirkDetails):
    relevant_liability = models.ForeignKey(Liability,
                                       on_delete=models.CASCADE)

class TraitValue(models.Model):
    relevant_stats = models.ForeignKey(ContractStats,
                                             on_delete=models.CASCADE)
    value = models.PositiveIntegerField()

    class Meta:
        abstract = True

class AttributeValue(TraitValue):
    relevant_attribute = models.ForeignKey(Attribute,
                                       on_delete=models.CASCADE)

class AbilityValue(TraitValue):
    relevant_ability = models.ForeignKey(Ability,
                                       on_delete=models.CASCADE)

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
    abilities = models.TextField(max_length=3000)
    secondary_abilities = models.TextField(max_length=3000)
    assets_and_liabilities = models.TextField(max_length=3000)