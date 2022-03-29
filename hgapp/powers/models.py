import uuid, json
from collections import defaultdict

from django.conf import settings
from django.db import models
from django.db.models import JSONField
from django.urls import reverse
from django.core.cache import cache
from django.core.files.base import ContentFile

from characters.models import Character, HIGH_ROLLER_STATUS, Attribute, Roll, NO_PARRY_INFO, NO_SPEED_INFO, DODGE_ONLY, \
    ATTACK_PARRY_TYPE, ROLL_SPEED, THROWN, Attribute, Ability, Weapon, WEAPON_MELEE, WEAPON_TYPE, Artifact
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

MOD_GIFT = "MOD_GIFT"
MOD_ACTIVATION = "MOD_ACTIVATION"
MOD_EFFECT = "MOD_EFFECT"
MODIFIER_CATEGORY = {
    (MOD_GIFT, "Gift Type"),
    (MOD_ACTIVATION, "Activation / Targeting"),
    (MOD_EFFECT, "Effect")
}

EPHEMERAL = "EPHEMERAL"
UNIQUE = "UNIQUE"
ADDITIVE = "ADDITIVE"
FIELD_SUBSTITUTION_MODE = (
    (EPHEMERAL, "Ephemeral"),
    (UNIQUE, "Unique"),
    (ADDITIVE, "Additive")
)

# for modifiers where there are details and multiplicity allowed.
SUB_JOINING_AND = "AND"
SUB_JOINING_OR = "OR"
SUB_ALL = "ALL"
SUB_MULTIPLE_STRATEGY = (
    (SUB_JOINING_AND, "Join using 'and'"),
    (SUB_JOINING_OR, "Join using 'or'"),
    (SUB_ALL, "Display all seperately"),
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

CRAFTING_NONE = 'NONCRAFTABLE'
CRAFTING_SIGNATURE = 'SIGNATURE ITEM'
CRAFTING_ARTIFACT = 'ARTIFACT_CRAFTING'
CRAFTING_CONSUMABLE = 'CONSUMABLE_CRAFTING'
CRAFTING_TYPE = (
    (CRAFTING_NONE, "Not craftable"),
    (CRAFTING_SIGNATURE, "Signature Item"),
    (CRAFTING_ARTIFACT, "Artifact Crafting"),
    (CRAFTING_CONSUMABLE, "Consumable Crafting"),
)

SYS_ALL = 'ALL'
SYS_LEGACY_POWERS = 'HOUSEGAMES15'
SYS_PS2 = 'PS2'
DICE_SYSTEM = (
    (SYS_ALL, 'All'),
    (SYS_LEGACY_POWERS, 'House Games 1.5'),
    (SYS_PS2, 'New Powers System'),
)

# System field roll choices
BODY_ = ("BODY", "Body")
MIND_ = ("MIND", "Mind")
PARRY_ = ("PARRY", "Dodge or Defend")


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


class FieldSubstitutionMarker(models.Model):
    marker = models.SlugField(max_length=50, primary_key=True)

    def __str__(self):
        return self.marker


# abstract class to be sub-classed by the many-to-many tables connecting components to FieldSubstitionMarkers
class FieldSubstitution(models.Model):
    relevant_marker = models.ForeignKey(FieldSubstitutionMarker,
                                        on_delete=models.CASCADE)
    replacement = models.CharField(max_length=350, blank=True,
                                   help_text="A '$' in this string will be replaced with user input")
    mode = models.CharField(choices=FIELD_SUBSTITUTION_MODE, default=ADDITIVE, max_length=25)

    class Meta:
        abstract = True

    def __str__(self):
        return "[[{}]] {} ({})".format(self.relevant_marker, self.get_mode_display(), self.replacement)

    def save(self, *args, **kwargs):
        super(FieldSubstitution, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def to_blob(self):
        return {
            "marker": self.relevant_marker.marker,
            "replacement": self.replacement,
            "mode": self.mode,
        }


class EnhancementFieldSubstitution(FieldSubstitution):
    relevant_enhancement = models.ForeignKey("Enhancement", on_delete=models.PROTECT)


class DrawbackFieldSubstitution(FieldSubstitution):
    relevant_drawback = models.ForeignKey("Drawback", on_delete=models.PROTECT)


class ParameterFieldSubstitution(FieldSubstitution):
    relevant_parameter = models.ForeignKey("Parameter", on_delete=models.PROTECT)


class BasePowerFieldSubstitution(FieldSubstitution):
    relevant_base_power = models.ForeignKey("Base_Power", on_delete=models.PROTECT)


class EnhancementGroup(models.Model):
    label = models.CharField(max_length=80)
    min_required = models.IntegerField("Num Enhancements Required",
                                       blank=True,
                                       null=True,
                                       help_text="if specified, the minimum number of required enhancements of this group."
                                                 " For example, informational enhancements or commune enhancements")
    seasoned_threshold = models.IntegerField("Seasoned Threshold",
                                       blank=True,
                                         null=True,
                                       help_text="Requires Seasoned to take this many enhancements of this group")
    veteran_threshold = models.IntegerField("Veteran Threshold",
                                             blank=True,
                                            null=True,
                                             help_text="Requires Veteran to take this many enhancements of this group")

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        super(EnhancementGroup, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def to_blob(self):
        return {
            "pk": self.pk,
            "label": self.label,
            "min_required": self.min_required,
            "seasoned_threshold": self.seasoned_threshold,
            "veteran_threshold": self.veteran_threshold,
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
    category = models.CharField(choices=MODIFIER_CATEGORY,
                                max_length=30,
                                default=MOD_EFFECT,
                                help_text="For filtering on create gift page")
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
    multiple_sub_strategy = models.CharField(choices=SUB_MULTIPLE_STRATEGY,
                                             default=SUB_JOINING_AND,
                                             max_length=55,
                                             help_text="When a modifier has multiplicity allowed and details, this " +
                                                       "specifies how the details should be joined before they are subbed.")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name + " [" + self.slug + "] (" + self.description + ")"

    def save(self, *args, **kwargs):
        super(Modifier, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def display(self):
        return self.name + " (" + self.description + ")"

    def to_blob(self):
        return {
            "name": self.name,
            "slug": self.slug,
            'required_enhancements': [x.pk for x in self.required_Enhancements.all()],
            'required_drawbacks': [x.pk for x in self.required_drawbacks.all()],
            "required_status": [self.required_status, self.get_required_status_display()],
            "category": self.category,
            "description": self.description,
            "eratta": self.eratta,
            "multiplicity_allowed": self.multiplicity_allowed,
            "detail_field_label": self.detail_field_label,
            "joining_strategy": self.multiple_sub_strategy,
        }


class Enhancement(Modifier):
    substitutions = models.ManyToManyField(FieldSubstitutionMarker,
                                           through=EnhancementFieldSubstitution,
                                           through_fields=('relevant_enhancement', 'relevant_marker'))
    group = models.ForeignKey(EnhancementGroup,
                              blank=True,
                              null=True,
                              on_delete=models.CASCADE)

    def to_blob(self):
        field_blob = super(Enhancement, self).to_blob()
        # If no substitutions, add a "default" substitution.
        if self.substitutions.count() == 0:
            default_sub = {
                "marker": "additional-effects",
                "replacement": self.description,
                "mode": ADDITIVE,
            }
            sub_list = [default_sub]
        else:
            substitutions = self.enhancementfieldsubstitution_set.select_related("relevant_marker").all()
            sub_list = [x.to_blob() for x in substitutions]
        enh_blob = {
            "substitutions": sub_list,
            "group": self.group.pk if self.group else None,
        }
        field_blob.update(enh_blob)
        return field_blob

    def form_name(self):
        return self.slug + "-e-is_selected"

    def form_detail_name(self):
        return self.slug + "-e-detail_text"


class Drawback(Modifier):
    substitutions = models.ManyToManyField(FieldSubstitutionMarker,
                                           through=DrawbackFieldSubstitution,
                                           through_fields=('relevant_drawback', 'relevant_marker'))

    def to_blob(self):
        field_blob = super(Drawback, self).to_blob()
        # If no substitutions, add a "default" substitution.
        if self.substitutions.count() == 0:
            default_sub = {
                "marker": "additional-restrictions",
                "replacement": self.description,
                "mode": ADDITIVE,
            }
            sub_list = [default_sub]
        else:
            substitutions = self.drawbackfieldsubstitution_set.select_related("relevant_marker").all()
            sub_list = [x.to_blob() for x in substitutions]
        sub_blob = {
            "substitutions": sub_list
        }
        field_blob.update(sub_blob)
        return field_blob

    def form_name(self):
        return self.slug + "-d-is_selected"

    def form_detail_name(self):
        return self.slug + "-d-detail_text"


class Parameter(models.Model):
    name = models.CharField(max_length= 50)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length=50,
                            primary_key = True)
    substitutions = models.ManyToManyField(FieldSubstitutionMarker,
                                           through=ParameterFieldSubstitution,
                                           through_fields=('relevant_parameter', 'relevant_marker'))
    attribute_bonus = models.ForeignKey(Attribute,
                                        blank=True,
                                        null=True,
                                        on_delete=models.CASCADE)

    # LEGACY FIELDS, IGNORED IN Power SYSTEM 2
    level_zero = models.CharField(max_length= 60,
                                  help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")
    level_one = models.CharField(max_length= 60,
                                 blank=True,
                                 null=True,
                                 help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")
    level_two = models.CharField(max_length= 60,
                                 blank=True,
                                 null=True,
                                 help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")
    level_three = models.CharField(max_length= 60,
                                   blank=True,
                                   null=True,
                                   help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")
    level_four = models.CharField(max_length= 60,
                                  blank=True,
                                  null=True,
                                  help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")
    level_five = models.CharField(max_length= 60,
                                  blank=True,
                                  null=True,
                                  help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")
    level_six = models.CharField(max_length= 60,
                                 blank=True,
                                 null=True,
                                 help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")
    eratta = models.TextField(blank=True,
                              null=True,
                              help_text="IGNORED IN NEW POWERS SYSTEM. Use field on Power_Param instead.")

    def display(self):
        return " ".join([self.name])

    def __str__(self):
        return " ".join([self.name]) + " [" +self.slug + "]"

    def save(self, *args, **kwargs):
        super(Parameter, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

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
        if level == 0:
            return self.level_zero
        if level == 1:
            return self.level_one
        if level == 2:
            return self.level_two
        if level == 3:
            return self.level_three
        if level == 4:
            return self.level_four
        if level == 5:
            return self.level_five
        if level == 6:
            return self.level_six
        raise ValueError

    def get_max_level(self):
        for n in range(7):
            if self.get_value_for_level(n) is None:
                return n
        return 7

    def to_blob(self):
        # If no substitutions, add a "default" substitution.
        field_blob = {
            "name": self.name,
        }
        if self.substitutions.count() == 0:
            default_sub = {
                "marker": self.slug,
                "replacement": "$",
                "mode": UNIQUE,
            }
            sub_list = [default_sub]
        else:
            substitutions = self.parameterfieldsubstitution_set.select_related("relevant_marker").all()
            sub_list = [x.to_blob() for x in substitutions]
        field_blob["substitutions"] = sub_list
        return field_blob


class Base_Power_Category(models.Model):
    name = models.CharField(max_length = 25)
    slug = models.SlugField("Unique URL-Safe Name",
                            max_length = 25,
                            primary_key= True)
    description = models.CharField(max_length = 50)
    color = models.CharField(max_length=8, default="#111418")

    def __str__(self):
        return " ".join([self.name])

    def save(self, *args, **kwargs):
        super(Base_Power_Category, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def container_class(self):
        return "css-cat-container-" + self.slug

    def to_blob(self):
        return {
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "container_class": self.container_class(),
            "components": list(self.base_power_set.order_by("name").values_list("pk", flat=True)),
        }


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
    substitutions = models.ManyToManyField(FieldSubstitutionMarker,
                                           through=BasePowerFieldSubstitution,
                                           through_fields=('relevant_base_power', 'relevant_marker'))
    icon = models.FileField(blank=True)

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
                                             help_text="Set on Effects and Modalities only. Ignored on Vectors.")
    allowed_modalities = models.ManyToManyField("Base_Power",
                                                related_name="vector_modalities",
                                                blank=True,
                                                help_text="Set on Effects only. Ignored on Vectors and Modalities." )
    vector_cost_credit = models.ManyToManyField("Base_Power",
                                                through="VectorCostCredit",
                                                through_fields=('relevant_effect', 'relevant_vector'),
                                                help_text="SET ON EFFECTS ONLY. Any Gift using this Effect and the "
                                                          "listed Vector will be reduced in cost by the credit.")

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
    crafting_type = models.CharField(choices=CRAFTING_TYPE, default=CRAFTING_NONE, max_length=45)

    class Meta:
        verbose_name = "Gift Component"

    def __str__(self):
        return self.name + " (" + self.summary + ")"

    def save(self, *args, **kwargs):
        super(Base_Power, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

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
        weapon_fields = system.systemfieldweapon_set.all() if system else None
        return {
            'slug': self.slug,
            'name': self.name,
            'summary': self.summary,
            'description': self.description,
            'eratta': self.eratta,
            'type': self.base_type,
            'gift_credit': self.num_free_enhancements,
            'required_status': self.required_status,
            'icon_url': self.icon.url if self.icon else "",
            'category': self.category.pk if self.category else None,
            'substitutions': [x.to_blob() for x in self.basepowerfieldsubstitution_set.all()],
            'allowed_vectors': list(self.allowed_vectors.values_list('pk', flat=True)),
            'allowed_modalities': list(self.allowed_modalities.values_list('pk', flat=True)),
            'enhancements': list(self.avail_enhancements.values_list('pk', flat=True)),
            'drawbacks': list(self.avail_drawbacks.values_list('pk', flat=True)),
            'parameters': [x.to_blob() for x in self.power_param_set.exclude(dice_system=SYS_LEGACY_POWERS).select_related("relevant_parameter").all()],
            'blacklist_enhancements': list(self.blacklist_enhancements.values_list("pk", flat=True)),
            'blacklist_drawbacks': list(self.blacklist_drawbacks.values_list("pk", flat=True)),
            'blacklist_parameters': list(self.blacklist_parameters.values_list("pk", flat=True)),
            'system_text': system.system_text if system else None,
            'default_description_prompt': system.default_description_prompt if system else None,
            'text_fields': [x.to_blob() for x in text_fields] if text_fields else [],
            'roll_fields': [x.to_blob() for x in roll_fields] if roll_fields else [],
            'weapon_fields': [x.to_blob() for x in weapon_fields] if weapon_fields else [],
        }


class VectorCostCredit(models.Model):
    relevant_vector = models.ForeignKey(Base_Power, on_delete=models.CASCADE, related_name="cost_vector")
    relevant_effect = models.ForeignKey(Base_Power, on_delete=models.CASCADE, related_name="cost_effect")
    gift_credit = models.IntegerField("Gift Credit",
                                      help_text="The cost of any Gift using this combination of Effect and Vector is "
                                                "reduced by this amount.")

    def __str__(self):
        return ":".join([self.relevant_vector.name, self.relevant_effect.name, str(self.gift_credit)])

    def save(self, *args, **kwargs):
        super(VectorCostCredit, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def to_blob(self):
        return {
            "vector": self.relevant_vector.pk,
            "effect": self.relevant_effect.pk,
            "credit": self.gift_credit,
        }


# class for system for components (Modality, Vector, Effect)
class Base_Power_System(models.Model):
    dice_system = models.CharField(choices=DICE_SYSTEM,
                                   max_length=55,
                                   default=SYS_PS2)
    system_text = models.TextField(help_text="((marker1,marker2)) : join markers with 'and'.<br>"
                                             "@@marker1,marker2%% : join markers with 'or'.<br>"
                                             "((marker))^ or @@marker%%^ : join as list and capitalize first character. <br>"
                                             "[[marker|default]] : replace marker, or use default if no replacement.<br>"
                                             "[[marker]] : replace marker or blank if no replacement.<br>"
                                             ";;marker// : replace marker with bulleted list.<br>"
                                             "##marker1,marker2++ : sum the markers together and display the result.<br>"
                                             "{{marker}} : replace marker, paragraph breaks between multiple entries.")
    eratta = models.TextField(blank=True,
                              null=True)
    default_description_prompt = models.TextField(blank=True,
                                                  null=True)
    base_power = models.ForeignKey(Base_Power,
                                   on_delete=models.PROTECT)
    class Meta:
        unique_together = (("base_power", "dice_system"))

    def save(self, *args, **kwargs):
        super(Base_Power_System, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def __str__(self):
        return ":".join([self.base_power.name, str(self.dice_system)])


# Joining between Parameter and Componeent
class Power_Param(models.Model):
    relevant_parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=55, default=SYS_PS2)
    seasoned = models.IntegerField("Seasoned Threshold" )
    veteran = models.IntegerField("Veteran Threshold")
    default = models.IntegerField("Default Level")
    relevant_base_power = models.ForeignKey(Base_Power, on_delete=models.CASCADE)

    # The following fields are only used by the PS2 power system
    level_zero = models.CharField(max_length=60,
                                  blank=True,
                                  null=True,
                                  help_text="Only used by new Powers system. Ignored in old system.")
    level_one = models.CharField(max_length=60,
                                 blank=True,
                                 null=True,
                                 help_text="Only used by new Powers system. Ignored in old system.")
    level_two = models.CharField(max_length=60,
                                 blank=True,
                                 null=True,
                                 help_text="Only used by new Powers system. Ignored in old system.")
    level_three = models.CharField(max_length=60,
                                   blank=True,
                                   null=True,
                                   help_text="Only used by new Powers system. Ignored in old system.")
    level_four = models.CharField(max_length=60,
                                  blank=True,
                                  null=True,
                                  help_text="Only used by new Powers system. Ignored in old system.")
    level_five = models.CharField(max_length=60,
                                  blank=True,
                                  null=True,
                                  help_text="Only used by new Powers system. Ignored in old system.")
    level_six = models.CharField(max_length=60,
                                 blank=True,
                                 null=True,
                                 help_text="Only used by new Powers system. Ignored in old system.")
    eratta = models.TextField(blank=True,
                              null=True,
                              help_text="Only used by new Powers system. Ignored in old system.")

    class Meta:
        unique_together = ("relevant_parameter", "relevant_base_power", "dice_system")

    def __str__(self):
        return ":".join([str(self.relevant_parameter), self.relevant_base_power.name])

    def save(self, *args, **kwargs):
        super(Power_Param, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def to_blob(self):
        return {
            "id": self.pk,
            "param_id": self.relevant_parameter.pk,
            "levels": self.get_levels(),
            "eratta": self.eratta,
            "default_level": self.default,
            "seasoned_threshold": self.seasoned,
            "veteran_threshold": self.veteran,
        }

    def get_status_tag(self, level):
        switcher = {
            self.default: " (Default)",
            self.seasoned: " (Seasoned)",
            self.veteran: " (Veteran)",
        }
        if level in switcher:
            return switcher[level]
        else:
            return ""

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
        if level == 0:
            return self.level_zero
        if level == 1:
            return self.level_one
        if level == 2:
            return self.level_two
        if level == 3:
            return self.level_three
        if level == 4:
            return self.level_four
        if level == 5:
            return self.level_five
        if level == 6:
            return self.level_six
        raise ValueError

    def get_max_level(self):
        for n in range(7):
            if self.get_value_for_level(n) is None:
                return n
        return 7

# Power full is essentially a "Gift" object
class Power_Full(models.Model):
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=55)
    crafting_type = models.CharField(choices=CRAFTING_TYPE, default=CRAFTING_NONE, max_length=45)
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
    latest_rev = models.ForeignKey("Power",
                                   on_delete=models.CASCADE,
                                   blank=True,
                                   null=True)
    artifacts = models.ManyToManyField(Artifact,
                                       through="ArtifactPowerFull",
                                       through_fields=('relevant_power_full', 'relevant_artifact'))

    # Denormalized fields with Power revisions. Do not use these?
    base = models.ForeignKey(Base_Power, on_delete=models.PROTECT)
    name = models.CharField(max_length=500)

    # Fields for Stock Gifts
    tags = models.ManyToManyField(PowerTag, blank=True)
    example_description = models.CharField(max_length=9000,
                                           blank=True,
                                           null=True)

    class Meta:
        permissions = (
            ('view_private_power_full', 'View private power full'),
            ('edit_power_full', 'Edit power full'),
        )
        indexes = [
            models.Index(fields=['owner', 'is_deleted', 'dice_system']),
            models.Index(fields=['character', 'dice_system']),
        ]
        verbose_name = "Gift"

    def delete(self):
        self.character = None
        for reward in self.reward_list():
            reward.refund_keeping_character_assignment()
        self.is_deleted = True
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

    def get_gift_cost(self):
        return self.latest_revision().get_gift_cost()

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

    def is_ps2(self):
        return self.dice_system == SYS_PS2

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


# TODO: remove permissioning from this and use Power_Full permissioning.
class Power(models.Model):
    name = models.CharField(max_length=150)
    flavor_text = models.TextField(max_length=2000) # tagline
    description = models.TextField("visual description", max_length=2500)
    extended_description = models.TextField(max_length=8000, blank=True)
    gift_summary = models.TextField("gift summary", max_length=2500, default="") #rendered "you possess a power to eat chips" etc.
    warnings = JSONField("Gift Warnings", default=list)
    dice_system = models.CharField(choices=DICE_SYSTEM, max_length=55)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.CASCADE,
                                   blank=True,
                                   null=True)
    pub_date = models.DateTimeField('date published', auto_now_add=True)

    gift_cost = models.IntegerField(null=True) # denormalized, access with get_gift_cost()
    required_status = models.CharField(choices=HIGH_ROLLER_STATUS,
                                       max_length=25,
                                       blank=True)

    # Crafting
    artifacts = models.ManyToManyField(Artifact,
                                       through="ArtifactPower",
                                       through_fields=('relevant_power', 'relevant_artifact'))
    # Structure and system
    system = models.TextField(max_length=54000,
                              blank=True,
                              null=True) # HTML rendered system text, safe to display
    errata = models.TextField(max_length=54000, blank=True, default="") # HTML rendered errata, safe to display
    base = models.ForeignKey(Base_Power, on_delete=models.CASCADE, blank=True, null=True, related_name="power_effect")
    vector = models.ForeignKey(Base_Power, on_delete=models.CASCADE, blank=True, null=True, related_name="power_vector")
    modality = models.ForeignKey(Base_Power, on_delete=models.CASCADE, blank=True, null=True, related_name="power_modality")
    selected_enhancements = models.ManyToManyField(Enhancement,
                                                   blank=True,
                                                   through="Enhancement_Instance",
                                                   through_fields=('relevant_power', 'relevant_enhancement'))
    selected_drawbacks = models.ManyToManyField(Drawback,
                                                blank=True,
                                                through="Drawback_Instance",
                                                through_fields=('relevant_power', 'relevant_drawback'))
    parameter_values = models.ManyToManyField(Power_Param,
                                              through="Parameter_Value",
                                              through_fields=('relevant_power', 'relevant_power_param'))
    enhancement_names = JSONField("Enhancement Names", default=list)
    drawback_names = JSONField("Drawback Names", default=list)
    shouldDisplayVector = models.BooleanField(default=False) # I can't believe I used camel case here.

    # note: Access system field instances through reverse lookups

    # REVISIONING
    creation_reason = models.CharField(choices=CREATION_REASON, max_length=25)
    creation_reason_expanded_text = models.TextField(max_length=1500,
                                                     blank=True,
                                                     null=True)
    # TODO: remove blank=True null=True after migration
    parent_power = models.ForeignKey(Power_Full,
                                     blank=True,
                                     null=True,
                                     on_delete=models.CASCADE)

    # UNUSED FIELDS?
    # Maybe someday this can be used with character sheet integrations for passive/active powers that may sometimes
    # be on or off
    activation_style = models.CharField(choices=ACTIVATION_STYLE, max_length=25, default=ACTIVATION_STYLE[0][0])

    # FIELDS THAT SHOULD BE REMOVED
    # Power_full should be responsible for privacy controls and probably ownership as well.
    private = models.BooleanField(default=False)

    class Meta:
        constraints = [
        ]
        permissions = (
            ('view_private_power', 'View private power'),
        )
        indexes = [
            models.Index(fields=['parent_power', 'pub_date']),
        ]

    def __str__(self):
        return self.name + " (" + self.description + ")"

    def get_enhancement_list(self):
        return "<b>Enhancements:</b><br>{}".format("<br>".join(self.enhancement_names))

    def get_num_enhancements(self):
        return len(self.enhancement_names)

    def get_drawback_list(self):
        return "<b>Drawbacks:</b><br>{}".format("<br>".join(self.drawback_names))

    def get_num_drawbacks(self):
        return len(self.drawback_names)

    #TODO: this seems to be for base powers??/
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
        new_power = not self.pk
        if self.dice_system != SYS_PS2:
            if hasattr(self, "system") and self.system:
                if self.system == self.base.get_system().system_text:
                    self.system = None
        super(Power, self).save(*args, **kwargs)
        if new_power and hasattr(self, "parent_power") and self.parent_power:
            parent = self.parent_power
            parent.latest_rev = self
            parent.save()

    def to_edit_blob(self):
        return {
            "effect_pk": self.base.pk,
            "vector_pk": self.vector.pk,
            "modality_pk": self.modality.pk,
            "name": self.name,
            "flavor_text": self.flavor_text,
            "description": self.description,
            "extended_description": self.extended_description,

            "enhancements": [x.to_blob() for x in self.enhancement_instance_set.all()],
            "drawbacks": [x.to_blob() for x in self.drawback_instance_set.all()],
            "parameters": [x.to_blob() for x in self.parameter_value_set.all()],

            "text_fields": [x.to_blob() for x in self.systemfieldtextinstance_set.all()] if hasattr(self, 'systemfieldtextinstance_set') else None,
            "roll_fields": [x.to_blob() for x in self.systemfieldrollinstance_set.all()] if hasattr(self, 'systemfieldrollinstance_set') else None,
            "weapon_fields": [x.to_blob() for x in self.systemfieldweaponinstance_set.all()] if hasattr(self, 'systemfieldweaponinstance_set') else None,
        }

    def get_gift_cost(self):
        if hasattr(self, "gift_cost") and self.gift_cost:
            return self.gift_cost
        else:
            self.gift_cost = self._get_point_value()
            self.save()
            return self.gift_cost

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

    def _get_point_value(self):
        cost_of_power = 1
        total_parameter_cost = 0
        for param_val in self.parameter_value_set.all():
            total_parameter_cost = total_parameter_cost + (param_val.value - param_val.relevant_power_param.default)
        cost_of_power = cost_of_power \
                + self.selected_enhancements.count() \
                - self.base.num_free_enhancements \
                - self.selected_drawbacks.count() \
                + total_parameter_cost
        if self.dice_system == SYS_PS2:
            cost_of_power = cost_of_power - self.vector.num_free_enhancements - self.modality.num_free_enhancements
            extra_credit = get_object_or_none(VectorCostCredit, relevant_vector=self.vector, relevant_effect=self.base)
            if extra_credit:
                cost_of_power = cost_of_power - extra_credit.gift_credit
        return cost_of_power


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
        output = output.format(self.name, self.get_gift_cost(), self.get_activation_style_display(), self.base.name, self.created_by.username)
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


class ArtifactPower(models.Model):
    relevant_artifact = models.ForeignKey(Artifact, on_delete=models.PROTECT)
    relevant_power = models.ForeignKey(Power, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ("relevant_artifact", "relevant_power"),
        )


class ArtifactPowerFull(models.Model):
    relevant_artifact = models.ForeignKey(Artifact, on_delete=models.PROTECT)
    relevant_power_full = models.ForeignKey(Power_Full, on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            ("relevant_artifact", "relevant_power_full"),
        )

class SystemField(models.Model):
    base_power_system = models.ForeignKey(Base_Power_System, on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    eratta = models.CharField(max_length=1000, blank=True, null=True)
    relevant_marker = models.ForeignKey(FieldSubstitutionMarker,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True,
                                        help_text="If not specified, this is the name of the field slugified.")
    replacement = models.CharField(max_length=350, blank=True,
                                   help_text="A '$' in this string will be replaced with user input. Defaults to '$' if empty.")

    def __str__(self):
        base_name = self.base_power_system.base_power.name
        return "{} [{}]".format(self.name, base_name)

    class Meta:
        unique_together = (("base_power_system", "name"))
        abstract = True

    def save(self, *args, **kwargs):
        super(SystemField, self).save(*args, **kwargs)
        PowerSystem.get_singleton().mark_dirty()

    def to_blob(self):
        return {
            "marker": self.relevant_marker.marker if self.relevant_marker else self.name.strip().lower().replace(" ", "-"),
            "replacement": self.replacement if self.replacement else "$",
            "id": self.pk,
            "name": self.name,
            "eratta": self.eratta,
        }

# SystemFieldRoll substitution should have [[defensive-roll-difficulty]]
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

    def get_choices(self):
        # returns a tuple of lists of tuples.
        # The first list is the choices for the "attribute selection" form
        # The second list are the choices for the "ability selection" form and may be empty if the field should not appear.
        attribute_choices = []
        ability_choices = []
        if self.allow_std_roll:
            if hasattr(self, "required_attribute") and self.required_attribute:
                required_attr = self.required_attribute
                attribute_choices.append((required_attr.pk, required_attr.name))
            else:
                attribute_choices.extend(
                    [(x.id, x.name) for x in Attribute.objects.filter(is_deprecated=False).order_by('name')])
            primary_abilities = Ability.objects.filter(is_primary=True).order_by('name')
            ability_choices = []
            ability_choices.extend([(x.id, x.name) for x in primary_abilities])
        if self.allow_parry:
            attribute_choices.append(PARRY_)
        if self.allow_mind:
            attribute_choices.append(MIND_)
        if self.allow_body:
            attribute_choices.append(BODY_)
        return attribute_choices, ability_choices

    def to_blob(self):
        attribute_choices, ability_choices = self.get_choices()
        roll_blob = {
            "attribute_choices": attribute_choices,
            "ability_choices": ability_choices,
            "parry_type": self.parry_type,
            "speed": self.speed,
        }
        field_blob = super(SystemFieldRoll, self).to_blob()
        field_blob.update(roll_blob)
        return field_blob


class SystemFieldText(SystemField):
    pass


class SystemFieldWeapon(SystemField):
    # blank for all weapon types allowed
    weapon_type = models.CharField(choices=WEAPON_TYPE,
                                   default=WEAPON_MELEE,
                                   max_length=30,
                                   blank=True,
                                   help_text="Provides the following substitutions based on the selected weapon: <br>"
                                             "selected-weapon-name, selected-weapon-type, selected-weapon-bonus-damage, "
                                             "selected-weapon-attack-roll, selected-weapon-attack-roll-difficulty, "
                                             "selected-weapon-attack-text, selected-weapon-range, "
                                             "selected-weapon-errata")

    def to_blob(self):
        weapons = Weapon.objects.filter(type=self.weapon_type).order_by("bonus_damage").all()
        weapon_choices = [(weap.pk, weap.name) for weap in weapons]
        choice_blob = {
            "weapon_choices": weapon_choices,
        }
        field_blob = super(SystemFieldWeapon, self).to_blob()
        field_blob.update(choice_blob)
        return field_blob

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

    def to_blob(self):
        return {
            "field_id": self.relevant_field.pk,
            "value": self.value
        }


class SystemFieldRollInstance(SystemFieldInstance):
    relevant_field = models.ForeignKey(SystemFieldRoll,
                                       on_delete=models.CASCADE)
    roll = models.ForeignKey(Roll, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("relevant_field", "relevant_power"))

    def to_blob(self):
        return {
            "field_id": self.relevant_field.pk,
            "roll_attribute": self._get_roll_initial_attribute(self.roll),
            "roll_ability": self._get_roll_initial_ability(self.roll),
        }

    def _get_roll_initial_ability(self, roll):
        if roll.ability:
            return [roll.ability.id, roll.ability.name]
        else:
            return None

    def _get_roll_initial_attribute(self, roll):
        if roll.attribute:
            return [roll.attribute.id, roll.attribute.name]
        elif roll.is_mind:
            return MIND_
        elif roll.is_body:
            return BODY_
        elif roll.parry_type != NO_PARRY_INFO:
            return PARRY_
        else:
            raise ValueError("Unknown roll attribute")

    def render_value(self):
        if self.relevant_field.caster_rolls:
            return self.roll.render_html_for_current_contractor()
        else:
            return self.roll.render_value_for_power()


class SystemFieldWeaponInstance(SystemFieldInstance):
    relevant_field = models.ForeignKey(SystemFieldWeapon, on_delete=models.CASCADE)
    weapon = models.ForeignKey(Weapon, on_delete=models.CASCADE)

    def to_blob(self):
        return {
            "field_id": self.relevant_field.pk,
            "weapon_id": self.weapon.pk,
        }


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

    def to_blob(self):
        return {
            "enhancement_slug": self.relevant_enhancement.pk,
            "detail": self.detail,
        }

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

    def to_blob(self):
        return {
            "drawback_slug": self.relevant_drawback.pk,
            "detail": self.detail,
        }

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

    def to_blob(self):
        return {
            "power_param_pk": self.relevant_power_param.pk,
            "value": self.value,
        }

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


class PowerSystem(models.Model):
    json_media = models.FileField(blank=True)
    revision = models.UUIDField(default=uuid.uuid4)

    @staticmethod
    def get_singleton():
        return PowerSystem.objects.get()

    def mark_dirty(self):
        self.revision = uuid.uuid4()
        self.save()

    def regenerate(self):
        python_blob = self._generate_python()
        self.revision = uuid.uuid4()
        self.json_media.save("power_system_json_{}.json".format(self.revision), ContentFile(json.dumps(python_blob).encode("utf-8"), name="power_blob.json"))
        cache.set(self._get_cache_key(), python_blob, timeout=None)
        self.save()
        return python_blob

    def get_json_url(self):
        if self.is_dirty():
            self.regenerate()
        return self.json_media.url

    def is_dirty(self):
        sentinel = object()
        cache_contents = cache.get(self._get_cache_key(), sentinel)
        return cache_contents is sentinel

    def get_python(self):
        if self.is_dirty():
            return self.regenerate()
        return cache.get(self._get_cache_key())

    def _get_cache_key(self):
        return "power_blob:{}".format(self.revision)

    @staticmethod
    def _generate_python():
        vectors = PowerSystem._generate_component_blob(VECTOR)
        effects = PowerSystem._generate_component_blob(EFFECT)
        modalities = PowerSystem._generate_component_blob(MODALITY)
        effects_by_modality = defaultdict(list)
        vectors_by_effect = defaultdict(list)
        vectors_by_modality = {}
        for effect in effects.values():
            for modality_key in effect["allowed_modalities"]:
                effects_by_modality[modality_key].append(effect["slug"])
            vectors_by_effect[effect["slug"]].extend(effect["allowed_vectors"])
        for modality in modalities.values():
            vectors_by_modality[modality["slug"]] = [x for x in modality["allowed_vectors"]]
        return {
            # Components by ID (slug)
            'vectors': vectors,
            'effects': effects,
            'modalities': modalities,

            # Enhancements and Drawbacks by ID (slug)
            'enhancements': PowerSystem._generate_modifier_blob(Enhancement),
            'drawbacks': PowerSystem._generate_modifier_blob(Drawback),

            # The parameters dictionary only contains the parameter's name and substitution.
            # The level info is on the gift components
            'parameters': PowerSystem._generate_param_blob(),

            'component_categories': PowerSystem._generate_component_category_blob(),

            # An Effect is only available on a given modality if it appears in this mapping.
            'effects_by_modality': effects_by_modality,

            # A Vector is only available on a given Modality + Effect if it appears in both mappings.
            'vectors_by_effect': vectors_by_effect,
            'vectors_by_modality': vectors_by_modality,

            'effect_vector_gift_credit': PowerSystem._generate_effect_vector_gift_credits_blob(),

            # Weapon choice system fields use a Weapon's pk as the non-display value. Stats in this blob by pk.
            'weapon_replacements_by_pk': PowerSystem._generate_weapons_blob(),

            'enhancement_group_by_pk': PowerSystem._generate_enhancement_groups_blob()
        }

        # generate the json blob for the fe and for backend form validation.
        # TODO: cache this in a wrapping method
        # Cache in per-component caches so it doesn't have to be regenerated as much?
        # TODO: invalidate cache when any relevant model (enhancement, base power) is saved.

    @staticmethod
    def _generate_component_blob(base_type):
        # TODO: select related and stuff.
        # TODO: filter on is_public=True
        components = Base_Power.objects.filter(base_type=base_type) \
            .order_by("name") \
            .prefetch_related("basepowerfieldsubstitution_set") \
            .prefetch_related("power_param_set").all()
        #TODO: Determine if these prefetches do anything
        # .prefetch_related("avail_enhancements") \
        # .prefetch_related("avail_drawbacks") \
        # .prefetch_related("blacklist_enhancements") \
        # .prefetch_related("blacklist_drawbacks") \
        # .all()
        return {x.pk: x.to_blob() for x in components}

    @staticmethod
    def _generate_modifier_blob(ModifierClass):
        related_field = "enhancementfieldsubstitution_set" if ModifierClass is Enhancement else "drawbackfieldsubstitution_set"
        modifiers = ModifierClass.objects.exclude(system=SYS_LEGACY_POWERS).prefetch_related(related_field).all()
        return {x.pk: x.to_blob() for x in modifiers}

    @staticmethod
    def _generate_param_blob():
        params = Parameter.objects \
            .prefetch_related("parameterfieldsubstitution_set").all()
        return {x.pk: x.to_blob() for x in params}

    @staticmethod
    def _generate_weapons_blob():
        weapons = Weapon.objects.all()
        return {x.pk: PowerSystem._replacements_from_weapon(x) for x in weapons}

    @staticmethod
    def _replacements_from_weapon(weapon):
        return [
            PowerSystem._replacement("selected-weapon-name", weapon.name),
            PowerSystem._replacement("selected-weapon-type", weapon.get_type_display()),
            PowerSystem._replacement("selected-weapon-attack-roll", weapon.attack_roll_replacement()),
            PowerSystem._replacement("selected-weapon-damage", str(weapon.bonus_damage)),
            PowerSystem._replacement("selected-weapon-range", weapon.range),
        ]

    @staticmethod
    def _replacement(marker, replacmeent):
        return {
            "marker": marker,
            "replacement": replacmeent,
            "mode": ADDITIVE
        }

    @staticmethod
    def _generate_component_category_blob():
        categories = Base_Power_Category.objects.order_by("name").all()
        return [x.to_blob() for x in categories]

    @staticmethod
    def _generate_effect_vector_gift_credits_blob():
        cost_credits = VectorCostCredit.objects.all()
        return [x.to_blob() for x in cost_credits]

    @staticmethod
    def _generate_enhancement_groups_blob():
        groups = EnhancementGroup.objects.all()
        return {x.pk: x.to_blob() for x in groups}
