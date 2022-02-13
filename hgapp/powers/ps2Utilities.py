import json
from collections import defaultdict

from django.db.models import Prefetch
from .models import SYS_ALL, SYS_LEGACY_POWERS, SYS_PS2, EFFECT, VECTOR, MODALITY, Base_Power, Enhancement, Drawback, \
    Power_Param, Parameter, Base_Power_Category, VectorCostCredit, ADDITIVE, EnhancementGroup
from characters.models import Weapon

def generate_json_blob():
    return json.dumps(generate_power_blob())



def generate_power_blob():
    vectors = _generate_component_blob(VECTOR)
    effects = _generate_component_blob(EFFECT)
    modalities = _generate_component_blob(MODALITY)
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
        'enhancements': _generate_modifier_blob(Enhancement),
        'drawbacks': _generate_modifier_blob(Drawback),

        # The parameters dictionary only contains the parameter's name and substitution.
        # The level info is on the gift components
        'parameters': _generate_param_blob(),

        'component_categories': _generate_component_category_blob(),

        # An Effect is only available on a given modality if it appears in this mapping.
        'effects_by_modality': effects_by_modality,

        # A Vector is only available on a given Modality + Effect if it appears in both mappings.
        'vectors_by_effect': vectors_by_effect,
        'vectors_by_modality': vectors_by_modality,

        'effect_vector_gift_credit': _generate_effect_vector_gift_credits_blob(),

        # Weapon choice system fields use a Weapon's pk as the non-display value. Stats in this blob by pk.
        'weapon_replacements_by_pk': _generate_weapons_blob(),

        'enhancement_group_by_pk': _generate_enhancement_groups_blob()
    }

    # generate the json blob for the fe and for backend form validation.
    # TODO: cache this in a wrapping method
            # Cache in per-component caches so it doesn't have to be regenerated as much?
    # TODO: invalidate cache when any relevant model (enhancement, base power) is saved.

def _generate_component_blob(base_type):
    # TODO: select related and stuff.
    # TODO: filter on is_public=True
    components = Base_Power.objects.filter(base_type=base_type)\
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


def _generate_modifier_blob(ModifierClass):
    related_field = "enhancementfieldsubstitution_set" if ModifierClass is Enhancement else "drawbackfieldsubstitution_set"
    modifiers = ModifierClass.objects.exclude(system=SYS_LEGACY_POWERS).prefetch_related(related_field).all()
    return {x.pk: x.to_blob() for x in modifiers}


def _generate_param_blob():
    params = Parameter.objects\
        .prefetch_related("parameterfieldsubstitution_set").all()
    return {x.pk: x.to_blob() for x in params}


def _generate_weapons_blob():
    weapons = Weapon.objects.all()
    return {x.pk: _replacements_from_weapon(x) for x in weapons}


def _replacements_from_weapon(weapon):
    return [
        _replacement("selected-weapon-name", weapon.name),
        _replacement("selected-weapon-type", weapon.get_type_display()),
        _replacement("selected-weapon-attack-roll", weapon.attack_roll_replacement()),
        _replacement("selected-weapon-damage", str(weapon.bonus_damage)),
        _replacement("selected-weapon-range", weapon.range),
    ]

def _replacement(marker, replacmeent):
    return {
        "marker": marker,
        "replacement": replacmeent,
        "mode": ADDITIVE
    }

def _generate_component_category_blob():
    categories = Base_Power_Category.objects.order_by("name").all()
    return [x.to_blob() for x in categories]


def _generate_effect_vector_gift_credits_blob():
    cost_credits = VectorCostCredit.objects.all()
    return [x.to_blob() for x in cost_credits]

def _generate_enhancement_groups_blob():
    groups = EnhancementGroup.objects.all()
    return {x.pk: x.to_blob() for x in groups}
