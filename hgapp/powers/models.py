from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse

from characters.models import Character, HIGH_ROLLER_STATUS, Attribute, Roll, NO_PARRY_INFO, NO_SPEED_INFO, DODGE_ONLY, \
    ATTACK_PARRY_TYPE, ROLL_SPEED, THROWN, Attribute
from guardian.shortcuts import assign_perm, remove_perm
from django.utils.html import mark_safe, escape, linebreaks
from django.db.utils import IntegrityError
from hgapp.utilities import get_object_or_none

ACTIVATION_STYLE = (
    ('PASSIVE', 'Passive'),
    ('ACTIVE', 'Active'),
)

EFFECT = "EFFECT"
VECTOR = "VECTOR"
MODALITY = "MODALITY"
BASE_POWER_TYPE = (
    (EFFECT, 'Effect'),
    (VECTOR, 'Vector'),
    (MODALITY, 'Modality'),
)

EPHEMERAL = "EPHEMERAL"
UNIQUE = "UNIQUE"
ADDITIVE = "ADDITIVE"
FIELD_SUBSTITUTION_MODE = (
    (EPHEMERAL, "Ephemeral"),
    (UNIQUE, "Unique"),
    (ADDITIVE, "Additive")
)

CREATION_NEW = 'NEW'
CREATION_IMPROVEMENT = 'IMPROVEMENT'
CREATION_REVISION = "REVISION"
CREATION_ADJUSTMENT = 'ADJUSTMENT'
CREATION_REASON = (
    (CREATION_NEW, 'New'),
    (CREATION_IMPROVEMENT, 'Improvement'),
    (CREATION_REVISION, 'Revision'),
    (CREATION_ADJUSTMENT, 'Adjustment'),
)

SYS_ALL = 'ALL'
SYS_LEGACY_POWERS = 'HOUSEGAMES15'
SYS_PS2 = 'PS2'
DICE_SYSTEM = (
    (SYS_ALL, 'All'),
    (SYS_LEGACY_POWERS, 'House Games 1.5'),
    (SYS_PS2, 'New Powers System'),
)


class PowerTag(models.Model):
    tag = models.CharField(max_length=40)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=40,
                            primary_key=True)
    def __str__(self):
        return self.tag

class PremadeCategory(models.Model):
    name = models.CharField(max_length=500)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key=True)
    description = models.CharField(max_length=5000)
    is_generic = models.BooleanField(default=True)
    tags = models.ManyToManyField(PowerTag,
                                  blank=True)


class FieldSubstitution(models.Model):
    marker = models.SlugField(max_length=300)
    replacement = models.CharField(max_length=300, blank=True) # '$' in string to replace value
    mode = models.CharField(choices=FIELD_SUBSTITUTION_MODE, default=ADDITIVE, max_length=25)

    def __str__(self):
        return "[[{}]] {} ({})".format(self.marker, self.get_mode_display(), self.replacement)

    def to_blob(self):
        return {
            "marker": self.marker,
            "replacement": self.replacement,
            "mode": self.mode,
        }

# Enhancements and Drawbacks
class Modifier(models.Model):
    name = models.CharField(max_length = 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length = 50,
                            primary_key = True)
    required_Enhancements = models.ManyToManyField("Enhancement",
                                                   blank = True)
    required_drawbacks = models.ManyToManyField("Drawback",
                                                blank=True)
    required_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=HIGH_ROLLER_STATUS[0][0])
    system = models.CharField(choices=DICE_SYSTEM,
                              max_length=55,
                              default=SYS_PS2)
    description = models.CharField(max_length= 250)
    eratta = models.TextField(blank=True,
                              null=True)
    multiplicity_allowed = models.BooleanField(default=False)
    detail_field_label = models.CharField(blank=True,
                                          null=True,
                                          max_length=35)
    is_general = models.BooleanField(default=False)
    substitutions = models.ManyToManyField(FieldSubstitution)

    def __str__(self):
        return self.name + " [" + self.slug + "] (" + self.description + ")"

    def display(self):
        return self.name + " (" + self.description + ")"

    class Meta:
        abstract = True

    def to_blob(self):
        substitutions = self.substitutions.all()
        if substitutions.count() == 0:
            default_sub = FieldSubstitution(
                marker=self.slug,
                replacement = self.description,
                mode = ADDITIVE
            )
            sub_list = [default_sub.to_blob()]
        else:
            sub_list = [x.to_blob() for x in self.substitutions.all()]
        return {
            "name": self.name,
            "slug": self.slug,
            'required_enhancements': [x.pk for x in self.required_Enhancements.all()],
            'required_drawbacks': [x.pk for x in self.required_drawbacks.all()],
            "required_status": self.required_status,
            "description": self.description,
            "eratta": self.eratta,
            "multiplicity_allowed": self.multiplicity_allowed,
            "detail_field_label": self.detail_field_label,
            'substitutions': sub_list,
        }


class Enhancement(Modifier):
    def form_name(self):
        return self.slug + "-e-is_selected"

    def form_detail_name(self):
        return self.slug + "-e-detail_text"


class Drawback(Modifier):
    def form_name(self):
        return self.slug + "-d-is_selected"

    def form_detail_name(self):
        return self.slug + "-d-detail_text"


class Parameter(models.Model):
    name = models.CharField(max_length= 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key = True)
    level_zero = models.CharField(max_length= 60)
    level_one = models.CharField(max_length= 60,
                                 blank=True,
                                 null=True)
    level_two = models.CharField(max_length= 60,
                                blank=True,
                                null=True)
    level_three = models.CharField(max_length= 60,
                                   blank=True,
                                   null=True)
    level_four = models.CharField(max_length= 60,
                                  blank=True,
                                  null=True)
    level_five = models.CharField(max_length= 60,
                                  blank=True,
                                  null=True)
    level_six = models.CharField(max_length= 60,
                                 blank=True,
                                 null=True)
    eratta = models.TextField(blank=True,
                              null=True)
    attribute_bonus = models.ForeignKey(Attribute,
                                  blank=True,
                                  null=True,
                                  on_delete=models.CASCADE)
    substitutions = models.ManyToManyField(FieldSubstitution)
    seasoned_level = models.IntegerField("Seasoned Threshold",
                                   default=-1,
                                   help_text="If legacy power system, this field is ignored. 8+ for no restriction.")
    veteran_level = models.IntegerField("Veteran Threshold",
                                  default=-1,
                                  help_text="If legacy power system, this field is ignored. 8+ for no restriction")
    default = models.IntegerField("Default Level",
                                  default=1,
                                  help_text="If legacy power system, this field is ignored. 8+ for no retriction")

    def display(self):
        return " ".join([self.name])

    def __str__(self):
        return " ".join([self.name]) + " [" +self.slug + "]"

    def to_blob(self):
        return {
            "name": self.name,
            "slug": self.slug,
            "levels": self.get_levels(),
            "eratta": self.eratta,
            "seasoned_level": self.seasoned_level,
            "veteran_level": self.veteran_level,
            "default": self.default,
            'substitutions': {x.marker: x.to_blob() for x in self.substitutions.all()},
        }

    def get_levels(self):
        levels = []
        if hasattr(self, "level_zero") and self.level_zero:
            levels.append(self.level_zero)
        if hasattr(self, "level_one") and self.level_one:
            levels.append(self.level_one)
        if hasattr(self, "level_two") and self.level_two:
            levels.append(self.level_two)
        if hasattr(self, "level_three") and self.level_three:
            levels.append(self.level_three)
        if hasattr(self, "level_four") and self.level_four:
            levels.append(self.level_four)
        if hasattr(self, "level_five") and self.level_five:
            levels.append(self.level_five)
        if hasattr(self, "level_six") and self.level_six:
            levels.append(self.level_six)
        return levels

    def get_value_for_level(self, level):
        if level is 0:
            return self.level_zero
        if level is 1:
            return self.level_one
        if level is 2:
            return self.level_two
        if level is 3:
            return self.level_three
        if level is 4:
            return self.level_four
        if level is 5:
            return self.level_five
        if level is 6:
            return self.level_six
        raise ValueError

    def get_max_level(self):
        for n in range(7):
            if self.get_value_for_level(n) is None:
                return n
        return 7


class Base_Power_Category(models.Model):
    name = models.CharField(max_length = 25)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length = 25,
                            primary_key= True)
    description = models.CharField(max_length = 50)

    def __str__(self):
        return " ".join([self.name])


# class for Gift Modality, Vector, Effect
class Base_Power(models.Model):
    name = models.CharField(max_length= 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key = True)
    summary = models.CharField(max_length=50)
    description = models.TextField(max_length=5000)
    eratta = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    num_free_enhancements = models.IntegerField("gift point credit", default=0)
    substitutions = models.ManyToManyField(FieldSubstitution, verbose_name="Field substitutions", blank=True)

    # Component type, Effect, Modality, or Vector
    base_type = models.CharField(choices=BASE_POWER_TYPE,
                                 max_length=25,
                                 default=EFFECT,
                                 verbose_name="component type",
                                 help_text="DO NOT CHANGE THIS AFTER INITIAL CREATION")

    # Legacy v1 power system
    enhancements = models.ManyToManyField(verbose_name="legacy enhancements", to=Enhancement,
                                          blank=True)
    drawbacks = models.ManyToManyField(verbose_name="legacy drawbacks", to=Drawback,
                                       blank=True)

    # V2 Power system only
    allowed_vectors = models.ManyToManyField("Base_Power",
                                             related_name="vector_effects",
                                             blank=True,
                                             help_text="Set on Effects and Modalities only. No effect on Vectors.")
    allowed_modalities = models.ManyToManyField("Base_Power",
                                                related_name="vector_modalities",
                                                blank=True,
                                                help_text="Set on Effects only. No effect on Vectors or Modalities." )

    avail_enhancements = models.ManyToManyField(Enhancement, verbose_name="enhancements",
                                                related_name="avail_enhancements",
                                                blank=True)
    avail_drawbacks = models.ManyToManyField(Drawback, verbose_name="drawbacks",
                                             related_name="avail_drawbacks",
                                             blank=True)
    blacklist_parameters = models.ManyToManyField(Parameter, related_name="blacklist_params",
                                                  blank=True)
    blacklist_enhancements = models.ManyToManyField(Enhancement,
                                                    related_name="blacklist_enhancements",
                                                    blank=True)
    blacklist_drawbacks = models.ManyToManyField(Drawback,
                                                 related_name="blacklist_drawbacks",
                                                 blank=True)

    required_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       default=HIGH_ROLLER_STATUS[0][0])
    category = models.ForeignKey(Base_Power_Category,
                                 on_delete=models.PROTECT,
                                 blank=True, null=True)
    parameters = models.ManyToManyField(Parameter,
                                        through="Power_Param",
                                        through_fields=('relevant_base_power', 'relevant_parameter'))

    class Meta:
        verbose_name = "Gift Component"

    def __str__(self):
        return self.name + " (" + self.summary + ")"

    def get_absolute_url(self):
        return reverse('powers:powers_create_power', kwargs={'base_power_slug': self.slug})

    def example_powers(self):
        return Power_Full.objects.filter(base=self, tags__in=["example"])

    def used_power_fulls(self):
        return Power_Full.objects.filter(base=self, character__isnull=False, is_deleted=False)

    def get_system(self, system=SYS_LEGACY_POWERS):
        return get_object_or_none(Base_Power_System.objects.filter(dice_system=system, base_power=self))

    def to_blob(self):
        # Used by v2 powers system for passing to FE and on BE for form validation.
        system = self.get_system(SYS_PS2)
        text_fields = system.systemfieldtext_set.all() if system else None
        roll_fields = system.systemfieldroll_set.all() if system else None
        return {
            'slug': self.slug,
            'name': self.name,
            'summary': self.summary,
            'description': self.description,
            'eratta': self.eratta,
            'type': self.base_type,
            'gift_credit': self.num_free_enhancements,
            'required_status': self.required_status,
            'category': self.category.pk if self.category else None,
            'substitutions': {x.marker: x.to_blob() for x in self.substitutions.all()},
            'allowed_vectors': [x.pk for x in self.allowed_vectors.all()],
            'allowed_modalities': [x.pk for x in self.allowed_modalities.all()],
            'enhancements': [x.pk for x in self.avail_enhancements.all()],
            'drawbacks': [x.pk for x in self.avail_drawbacks.all()],
            'parameters': [x.relevant_parameter.pk for x in self.power_param_set.exclude(dice_system=SYS_LEGACY_POWERS).all()],
            'blacklist_enhancements': [x.pk for x in self.blacklist_enhancements.all()],
            'blacklist_drawbacks': [x.pk for x in self.blacklist_drawbacks.all()],
            'blacklist_parameters': [x.pk for x in self.blacklist_parameters.all()],
            'system_text': system.system_text if system else None,
            'text_fields': [x.to_blob() for x in text_fields] if text_fields else [],
            'roll_fields': [x.to_blob() for x in roll_fields] if roll_fields else [],
        }


# class for system for components (Modality, Vector, Effect)
class Base_Power_System(models.Model):
    dice_system = models.CharField(choices=DICE_SYSTEM,
                                   max_length=55,
                                   default=SYS_PS2)
    system_text = models.TextField()
    eratta = models.TextField(blank=True,
                              null=True)
    default_description_prompt = models.TextField(blank=True,
                                                  null=True)
    base_power = models.ForeignKey(Base_Power,
                                   on_delete=models.PROTECT)
    class Meta:
        unique_together = (("base_power", "dice_system"))

    def __str__(self):
        return ":".join([self.base_power.name, str(self.dice_system)])


# Joining between Parameter and Componeent
class Power_Param(models.Model):
    relevant_parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=55, default=SYS_PS2)
    seasoned = models.IntegerField("Seasoned Threshold",
                                   help_text="If v2 power system, this field is ignored.")
    veteran = models.IntegerField("Veteran Threshold",
                                  help_text="If v2 power system, this field is ignored.")
    default = models.IntegerField("Default Level",
                                  help_text="If v2 power system, this field is ignored.")
    relevant_base_power = models.ForeignKey(Base_Power, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("relevant_parameter", "relevant_base_power", "dice_system")

    def __str__(self):
        return ":".join([str(self.relevant_parameter), self.relevant_base_power.name])

    def get_status_tag(self, level):
        switcher = {
            self.default : " (Default)",
            self.seasoned : " (Seasoned)",
            self.veteran : " (Veteran)",
        }
        if level in switcher:
            return switcher[level]
        else:
            return ""


# Power full is essentially a "Gift" object
# Each Power_Full has at least one PowerHistory for an Effect/Vector and exactly one PowerHistory for a gift modality
    # Modality cost/credit is applied against all Effects on the gift
class Power_Full(models.Model):
    name = models.CharField(max_length = 500)
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=55)
    base = models.ForeignKey(Base_Power, on_delete=models.PROTECT)
    private = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True)
    character = models.ForeignKey(Character,
                                  blank=True,
                                  null=True,
                                  on_delete=models.CASCADE)
    tags = models.ManyToManyField(PowerTag, blank=True) # This is for stock Gifts
    example_description = models.CharField(max_length = 9000,
                                           blank=True,
                                           null=True)

    # TODO: Delete and replace with method that gives set of power histories
    latest_rev = models.ForeignKey("Power",
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True)

    class Meta:
        permissions = (
            ('view_private_power_full', 'View private power full'),
            ('edit_power_full', 'Edit power full'),
        )
        verbose_name = "Gift"

    def delete(self):
        self.character = None
        for reward in self.reward_list():
            reward.refund_keeping_character_assignment()
        self.is_deleted=True
        self.save()

    def save(self, *args, **kwargs):
        super(Power_Full, self).save(*args, **kwargs)
        if self.character:
            self.character.grant_initial_source_if_required()

    def player_manages_via_cell(self, player):
        if self.is_deleted:
            return False
        if self.character:
            if self.character.cell:
                if self.character.cell.player_can_edit_characters(player):
                    return True
        return False

    def player_can_edit(self, player):
        if self.is_deleted:
            return False
        is_owner = player == self.owner
        return is_owner or \
               self.player_manages_via_cell(player) or \
               (player.has_perm("edit_power_full", self) and self.player_can_view(player))

    def player_can_view(self, player):
        if self.is_deleted:
            return False
        is_owner = player == self.owner
        return is_owner or \
               not self.private or \
               player.has_perm("view_private_power_full", self) or \
               self.player_manages_via_cell(player)

    def latest_revision(self):
        if hasattr(self, "latest_rev") and self.latest_rev:
            return self.latest_rev
        else:
            self.latest_rev = self.power_set.order_by('-pub_date').first()
            self.save()
            return self.latest_rev

    def get_point_value(self):
        return self.power_set.order_by('-pub_date').all()[0].get_point_value()

    def set_self_and_children_privacy(self, is_private):
        if is_private:
            self.set_self_and_children_private()
        else:
            self.set_self_and_children_public()

    def set_self_and_children_private(self):
        self.private = True
        self.save()
        for power in self.power_set.all():
            power.private = True
            power.save()

    def reveal_history_to_player(self, player):
        assign_perm('view_power_full', player, self)
        assign_perm('view_private_power_full', player, self)
        for power in self.power_set.all():
            power.reveal_to_player(player)

    def lock_edits(self):
        remove_perm('powers.edit_power_full', self.owner)

    def default_perms_history_to_player(self, player):
        assign_perm('view_power_full', player, self)
        assign_perm('edit_power_full', player, self)
        if player != self.owner:
            remove_perm('view_private_power_full', player, self)
        for power in self.power_set.all():
            power.default_perms_to_player(player)

    def set_self_and_children_public(self):
        self.private = False
        self.save()
        for power in self.power_set.all():
            power.private = False
            power.save()

    def latest_archive_txt(self):
        return self.latest_revision().archive_txt()

    def reward_list(self):
        rewards = []
        for power in self.power_set.order_by("-pub_date").all():
            for reward in power.relevant_power.filter(is_void = False).order_by("-awarded_on").all():
                rewards.append(reward)
        return rewards

    def at_least_one_gift_assigned(self):
        for reward in self.reward_list():
            if not reward.is_improvement:
                return True
        return False

    def __str__(self):
        if self.owner:
            return self.name + " [" + self.owner.username + "]"
        else:
            return self.name + " [NO ASSOCIATED USER]"


# A given "revision track" of a Power.
# Multiple Powers may have the same PowerHistory, and the most recent one is the "canonical" one.
# A given Power_full may have multiple PowerHistorys
    # always has at least two in the new system (an Effect+Vector and a Gift Modality)
class PowerHistory(models.Model):
    parent_power = models.ForeignKey(Power_Full,
                                     blank=True,
                                     null=True,
                                     on_delete=models.CASCADE)
    latest_rev = models.ForeignKey("Power",
                                   on_delete=models.CASCADE,
                                   blank=True,
                                   null=True)


# TODO: remove permissioning from this and use Power_Full permissioning.
class Power(models.Model):
    name = models.CharField(max_length=150)
    flavor_text = models.TextField(max_length=2000)
    description = models.TextField(max_length=2500)

    # TODO: ensure power_history parent and parent_power are same.
    # TODO: remove blank=True null=True after migration
    parent_power = models.ForeignKey(Power_Full,
                                     blank=True,
                                     null=True,
                                     on_delete=models.CASCADE)

    # TODO: remove blank=True and null=True after migration
    power_history = models.ForeignKey(PowerHistory,
                                     blank=True,
                                     null=True,
                                     on_delete=models.CASCADE)
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=55)

    base = models.ForeignKey(Base_Power, on_delete=models.CASCADE, blank=True, null=True, related_name="power_effect")
    vector = models.ForeignKey(Base_Power, on_delete=models.CASCADE, blank=True, null=True, related_name="power_vector")
    modality = models.ForeignKey(Base_Power, on_delete=models.CASCADE, blank=True, null=True, related_name="power_modality")

    private = models.BooleanField(default=False)

    activation_style = models.CharField(choices=ACTIVATION_STYLE, max_length=25, default=ACTIVATION_STYLE[0][0])
    creation_reason = models.CharField(choices=CREATION_REASON, max_length=25)
    creation_reason_expanded_text = models.TextField(max_length=1500,
                                                     blank=True,
                                                     null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   blank=True,
                                   null=True)
    system = models.TextField(max_length = 14000,
                              blank=True,
                              null=True)
    selected_enhancements = models.ManyToManyField(Enhancement,
                                                   blank=True,
                                                   through="Enhancement_Instance",
                                                   through_fields=('relevant_power', 'relevant_enhancement'))
    selected_drawbacks = models.ManyToManyField(Drawback,
                                                   blank=True,
                                                   through="Drawback_Instance",
                                                   through_fields=('relevant_power', 'relevant_drawback'))
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    parameter_values = models.ManyToManyField(Power_Param,
                                              through="Parameter_Value",
                                              through_fields=('relevant_power', 'relevant_power_param'))

    class Meta:
        constraints = [
        ]
        permissions = (
            ('view_private_power', 'View private power'),
        )

    def __str__(self):
        return self.name + " (" + self.description + ")"

    def __check_constraints(self):
        if hasattr(self, "modality") and self.modality:
            if not self.modality.base_type == MODALITY:
                raise IntegrityError("Power modality must be modality base")
            if (hasattr(self, "base") and self.base) or (hasattr(self, "vector") and self.vector):
                raise IntegrityError("modality cannot have effect or vector set")
        if hasattr(self, "vector") and self.vector:
            if not self.vector.base_type == VECTOR:
                raise IntegrityError("Power vector must be vector base")
        if hasattr(self, "base") and self.base:
            if not self.base.base_type == EFFECT:
                raise IntegrityError("Power effect must be effect base")
        if (hasattr(self, "base") and self.base or hasattr(self, "vector") and self.vector) and not (self.base and self.vector):
            raise IntegrityError("Power with effect or vector must have both")


    def save(self, *args, **kwargs):
        self.__check_constraints()
        new_power = not self.pk
        if hasattr(self, "system") and self.system:
            if self.system == self.base.get_system().system_text:
                self.system = None
        super(Power, self).save(*args, **kwargs)
        if new_power and hasattr(self, "parent_power") and self.parent_power:
            parent = self.parent_power
            parent.latest_rev = self
            parent.save()

    def get_absolute_url(self):
        return reverse('powers:powers_view_power', kwargs={'power_id': self.pk})

    def get_system(self):
        if hasattr(self, "system") and self.system:
            return self.system
        else:
            return self.base.get_system().system_text

    def player_manages_via_cell(self, player):
        if self.parent_power:
            if self.parent_power.character:
                if self.parent_power.character.cell:
                    if self.parent_power.character.cell.player_can_edit_characters(player):
                        return True
        return False

    def player_can_edit(self, player):
        is_owner = player == self.created_by
        return is_owner or \
               self.player_manages_via_cell(player) or \
               (player.has_perm("edit_power", self) and self.player_can_view(player))

    def player_can_view(self, player):
        is_owner = player == self.created_by
        return is_owner or not self.private or player.has_perm("view_private_power", self) or self.player_manages_via_cell(player)

    def get_point_value(self):
        cost_of_power = 1
        total_parameter_cost = 0
        for param_val in self.parameter_value_set.all():
            total_parameter_cost = total_parameter_cost + (param_val.value - param_val.relevant_power_param.default)
        return  cost_of_power \
                + self.selected_enhancements.count() \
                - self.base.num_free_enhancements \
                - self.selected_drawbacks.count() \
                + total_parameter_cost

    def reveal_to_player(self, player):
        assign_perm('view_power', player, self)
        assign_perm('view_private_power', player, self)

    def default_perms_to_player(self, player):
        assign_perm('view_power', player, self)
        if player != self.created_by:
            remove_perm('view_private_power', player, self)

    def get_attribute_bonuses(self):
        bonuses = []
        params = self.parameter_value_set \
            .select_related('relevant_power_param__relevant_parameter')\
            .filter(relevant_power_param__relevant_parameter__attribute_bonus__isnull=False)\
            .all()
        for param in params:
            bonuses.append((param.relevant_power_param.relevant_parameter.attribute_bonus, int(param.get_level_description())))
        return bonuses


    def render_system(self):
        default_system = linebreaks(escape(self.get_system()))
        value_by_name = {param_val.relevant_power_param.relevant_parameter.name :
                             param_val.relevant_power_param.relevant_parameter.get_value_for_level(level=param_val.value)
                         for param_val in self.parameter_value_set.all()}
        for field_instance in self.systemfieldtextinstance_set.all():
            value_by_name[field_instance.relevant_field.name] = field_instance.render_value()
        for field_instance in self.systemfieldrollinstance_set.all():
            value_by_name[field_instance.relevant_field.name] = field_instance.render_value()
        rendered_system = default_system
        for name, value in value_by_name.items():
            replaceable_name = str.format("[[{}]]",
                                          name.lower().replace(" ", "-"))
            formatted_value = str.format("<b>{}</b>", value)

            rendered_system = rendered_system.replace(replaceable_name, formatted_value)
        return mark_safe(rendered_system)

    def archive_txt(self):
        output = "{}\nA {} point {} {} power\nCreated by {}\n"
        output = output.format(self.name, self.get_point_value(), self.get_activation_style_display(), self.base.name, self.created_by.username)
        output = output + "{}\nDescription: {}\nSystem: {}\n"
        output = output.format(self.flavor_text,self.description, self.get_system())
        output = output + "Parameters:\n-------------\n"
        for parameter_value in self.parameter_value_set.all():
            output = output + "{}"
            output = output.format(parameter_value.archive_txt())
        output = output + "Enhancements:\n-------------\n"
        for enhancement_instance in self.enhancement_instance_set.all():
            output = output + "{}"
            output = output.format(enhancement_instance.archive_txt())
        output = output + "Drawbacks:\n----------\n"
        for drawback_instance in self.drawback_instance_set.all():
            output = output + "{}"
            output = output.format(drawback_instance.archive_txt())
        return output

    def creation_reason_action_text(self):
        if self.creation_reason == CREATION_REASON[0][0]:
            return "new"
        if self.creation_reason == CREATION_REASON[1][0]:
            return "improving"
        if self.creation_reason == CREATION_REASON[2][0]:
            return "revising"
        if self.creation_reason == CREATION_REASON[3][0]:
            return "adjusting"


class SystemField(models.Model):
    base_power_system = models.ForeignKey(Base_Power_System, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    eratta = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        base_name = self.base_power_system.base_power.name
        return "{} [{}]".format(self.name, base_name)

    class Meta:
        unique_together = (("base_power_system", "name"))
        abstract = True

    def to_blob(self):
        return {
            "name": self.name,
            "eratta": self.eratta,
        }

class SystemFieldRoll(SystemField):
    allow_mind = models.BooleanField(default=False)
    allow_body = models.BooleanField(default=False)
    allow_std_roll = models.BooleanField(default=True)
    allow_parry = models.BooleanField(default=False)
    parry_type = models.CharField(choices=ATTACK_PARRY_TYPE,
                                  max_length=30,
                                  default=THROWN)
    speed = models.CharField(choices=ROLL_SPEED,
                             max_length=30,
                             default=NO_SPEED_INFO)
    required_attribute = models.ForeignKey(Attribute,
                                           on_delete=models.CASCADE,
                                           null=True,
                                           blank=True)
    difficulty = models.PositiveIntegerField(null=True,
                                             blank=True,
                                             help_text="Not used in new Powers system")
    caster_rolls = models.BooleanField(default=True)

    def render_speed(self):
        if self.speed == NO_SPEED_INFO:
            return None
        else:
            return self.get_speed_display()

    def to_blob(self):
        roll_blob = {
            "allow_mind": self.allow_mind,
            "allow_body": self.allow_body,
            "allow_std_roll": self.allow_std_roll,
            "allow_parry": self.allow_std_roll,
            "parry_type": self.parry_type,
            "speed": self.speed,
            "required_attribute": self.required_attribute,
        }
        field_blob = super(SystemFieldRoll, self)
        field_blob.update(roll_blob)
        return field_blob

class SystemFieldText(SystemField):
    pass


class SystemFieldInstance(models.Model):
    relevant_power = models.ForeignKey(Power, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class SystemFieldTextInstance(SystemFieldInstance):
    relevant_field = models.ForeignKey(SystemFieldText, on_delete=models.CASCADE)
    value = models.CharField(max_length = 1000,
                              null=True,
                              blank=True)

    class Meta:
        unique_together = (("relevant_field", "relevant_power"))

    def render_value(self):
        return escape(self.value)


class SystemFieldRollInstance(SystemFieldInstance):
    relevant_field = models.ForeignKey(SystemFieldRoll,
                                       on_delete=models.CASCADE)
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("relevant_field", "relevant_power"))

    def render_value(self):
        if self.relevant_field.caster_rolls:
            return self.roll.render_html_for_current_contractor()
        else:
            return self.roll.render_value_for_power()

class Enhancement_Instance(models.Model):
    relevant_enhancement = models.ForeignKey(Enhancement,
                                             on_delete=models.PROTECT)
    relevant_power = models.ForeignKey(Power,
                                       on_delete=models.CASCADE)
    detail = models.CharField(max_length=1500,
                              null=True,
                              blank=True)

    def archive_txt(self):
        output = "{} ({}) "
        output = output.format(self.relevant_enhancement.name, self.relevant_enhancement.description)
        if self.detail:
            output = output + "{}: {}"
            output = output.format(self.relevant_enhancement.detail_field_label, self.detail)
        output = output + "\n"
        return output

    def __str__(self):
        if self.relevant_enhancement.detail_field_label:
            return "{} :: {} {}: {}".format(self.relevant_power.name,str(self.relevant_enhancement), self.relevant_enhancement.detail_field_label, self.detail)
        else:
            return "{} :: {}".format(self.relevant_power.name,str(self.relevant_enhancement))



class Drawback_Instance(models.Model):
    relevant_drawback = models.ForeignKey(Drawback, on_delete=models.CASCADE)
    relevant_power = models.ForeignKey(Power,
                                       on_delete=models.CASCADE)
    detail = models.CharField(max_length=1500,
                              null=True,
                              blank=True)

    def archive_txt(self):
        output = "{} ({}) "
        output = output.format(self.relevant_drawback.name, self.relevant_drawback.description)
        if self.detail:
            output = output + "{}: {}"
            output = output.format(self.relevant_drawback.detail_field_label, self.detail)
        output = output + "\n"
        return output

    def __str__(self):
        if self.relevant_drawback.detail_field_label:
            return "{} :: {} {}: {}".format(self.relevant_power.name,str(self.relevant_drawback), self.relevant_drawback.detail_field_label, self.detail)
        else:
            return "{} :: {}".format(self.relevant_power.name,str(self.relevant_drawback))


class Parameter_Value(models.Model):
    relevant_power_param = models.ForeignKey(Power_Param, on_delete=models.CASCADE)

    relevant_power = models.ForeignKey(Power, on_delete=models.CASCADE)
    value = models.IntegerField()

    def __str__(self):
        return " ".join([str(self.relevant_power_param), str(self.relevant_power), str(self.value)])

    def get_level_description(self):
        return self.relevant_power_param.relevant_parameter.get_value_for_level(level=self.value)

    def archive_txt(self):
        output = "{}: level {} ({})\n"
        output = output.format(self.relevant_power_param.relevant_parameter.name, self.value, self.relevant_power_param.relevant_parameter.get_value_for_level(self.value))
        return output

    level_description = property(get_level_description)


class PowerTutorial(models.Model):
    modal_base = models.TextField(max_length=3000)
    modal_base_header = models.TextField(max_length=3000)
    modal_edit_header = models.TextField(max_length=3000)
    modal_edit = models.TextField(max_length=3000)
