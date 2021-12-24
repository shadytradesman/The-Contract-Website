import json
from .models import SYS_ALL, SYS_LEGACY_POWERS, SYS_PS2, EFFECT, VECTOR, MODALITY, Base_Power, Enhancement, Drawback

def generate_json_blob():
    return json.dumps(generate_power_blob())

def generate_power_blob():
    return {
        'vectors': _generate_component_blob(VECTOR),
        'effects': _generate_component_blob(EFFECT),
        'modalities': _generate_component_blob(MODALITY),
        'component_categories': _generate_component_category_blob(),
        'enhancements': _generate_modifier_blob(Enhancement),
        'drawbacks': _generate_modifier_blob(Drawback),
        'parameters': _generate_param_blob(),
    }

    #json_dumps dict
    pass
    # generate the json blob for the fe and for backend form validation.
    # TODO: cache this in a wrapping method
            # Cache in per-component caches so it doesn't have to be regenerated as much?
    # TODO: invalidate cache when any relevant model (enhancement, base power) is saved.

    # Return a map of maps
        # vectors:
            # id ->
                # (component details. Modifiers only so far as ID)
                # field substitutions are map from replacement string to other info
        # effects:
            # id ->
                # (component details. Modifiers only so far as ID)
        # enhancements
            # id -> enhancment info
        # drawbacks
            # id -> drawback info
        # parameters
            # flattened parameter / power_param info by ID

def _generate_component_blob(base_type):
    components = Base_Power.objects.filter(is_public=True, base_type=base_type).all()
    return {x.pk: x.to_blob() for x in components}
    # TODO: select related and stuff.
    # TODO: implement to_blob() on base_power


def _generate_modifier_blob(ModifierClass):
    ModifierClass.objects.exclude(system=SYS_LEGACY_POWERS).all()
    # Note this will include orphaned modifiers. Is this okay?
    pass


def _generate_param_blob():
    pass


def _generate_component_category_blob():
    pass
