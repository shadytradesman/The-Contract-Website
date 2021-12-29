import json
from collections import defaultdict
from .models import SYS_ALL, SYS_LEGACY_POWERS, SYS_PS2, EFFECT, VECTOR, MODALITY, Base_Power, Enhancement, Drawback, \
    Power_Param

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

        'parameters': _generate_param_blob(),

        'component_categories': _generate_component_category_blob(),

        # An Effect is only available on a given modality if it appears in this mapping.
        'effects_by_modality': effects_by_modality,

        #A Vector is only available on a given Modality + Effect if it appears in both mappings.
        'vectors_by_effect': vectors_by_effect,
        'vectors_by_modality': vectors_by_modality,
    }

    # generate the json blob for the fe and for backend form validation.
    # TODO: cache this in a wrapping method
            # Cache in per-component caches so it doesn't have to be regenerated as much?
    # TODO: invalidate cache when any relevant model (enhancement, base power) is saved.

def _generate_component_blob(base_type):
    # TODO: select related and stuff.
    components = Base_Power.objects.filter(is_public=True, base_type=base_type)\
        .prefetch_related("substitutions") \
        .prefetch_related("parameters") \
        .prefetch_related("avail_enhancements") \
        .prefetch_related("avail_drawbacks") \
        .all()
    return {x.pk: x.to_blob() for x in components}


def _generate_modifier_blob(ModifierClass):
    modifiers = ModifierClass.objects.exclude(system=SYS_LEGACY_POWERS).all()
    return {x.pk: x.to_blob() for x in modifiers}


def _generate_param_blob():
    power_params = Power_Param.objects.filter(dice_system=SYS_PS2).select_related("relevant_parameter").all()
    return {x.relevant_parameter.pk: x.relevant_parameter.to_blob() for x in power_params}


def _generate_component_category_blob():
    pass
