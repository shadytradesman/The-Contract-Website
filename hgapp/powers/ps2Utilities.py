import json
from collections import defaultdict

from django.forms import formset_factory
from django.db.models import Prefetch

from .models import SYS_ALL, SYS_LEGACY_POWERS, SYS_PS2, EFFECT, VECTOR, MODALITY, Base_Power, Enhancement, Drawback, \
    Power_Param, Parameter, Base_Power_Category, VectorCostCredit, ADDITIVE, EnhancementGroup
from .formsPs2 import PowerForm, ModifierForm, ParameterForm, SystemFieldTextForm, SystemFieldRollForm, \
    SystemFieldWeaponForm
from characters.models import Weapon


class PowerBlobGenerator:

    def __init__(self):
        self.blob = PowerBlobGenerator._generate_power_blob()

    def get_power_blob(self):
        return self.blob

    def get_json_power_blob(self):
        return json.dumps(self.get_power_blob())

    @staticmethod
    def _generate_power_blob():
        vectors = PowerBlobGenerator._generate_component_blob(VECTOR)
        effects = PowerBlobGenerator._generate_component_blob(EFFECT)
        modalities = PowerBlobGenerator._generate_component_blob(MODALITY)
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
            'enhancements': PowerBlobGenerator._generate_modifier_blob(Enhancement),
            'drawbacks': PowerBlobGenerator._generate_modifier_blob(Drawback),

            # The parameters dictionary only contains the parameter's name and substitution.
            # The level info is on the gift components
            'parameters': PowerBlobGenerator._generate_param_blob(),

            'component_categories': PowerBlobGenerator._generate_component_category_blob(),

            # An Effect is only available on a given modality if it appears in this mapping.
            'effects_by_modality': effects_by_modality,

            # A Vector is only available on a given Modality + Effect if it appears in both mappings.
            'vectors_by_effect': vectors_by_effect,
            'vectors_by_modality': vectors_by_modality,

            'effect_vector_gift_credit': PowerBlobGenerator._generate_effect_vector_gift_credits_blob(),

            # Weapon choice system fields use a Weapon's pk as the non-display value. Stats in this blob by pk.
            'weapon_replacements_by_pk': PowerBlobGenerator._generate_weapons_blob(),

            'enhancement_group_by_pk': PowerBlobGenerator._generate_enhancement_groups_blob()
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
        return {x.pk: PowerBlobGenerator._replacements_from_weapon(x) for x in weapons}

    @staticmethod
    def _replacements_from_weapon(weapon):
        return [
            PowerBlobGenerator._replacement("selected-weapon-name", weapon.name),
            PowerBlobGenerator._replacement("selected-weapon-type", weapon.get_type_display()),
            PowerBlobGenerator._replacement("selected-weapon-attack-roll", weapon.attack_roll_replacement()),
            PowerBlobGenerator._replacement("selected-weapon-damage", str(weapon.bonus_damage)),
            PowerBlobGenerator._replacement("selected-weapon-range", weapon.range),
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


def get_edit_context(existing_power=None):
    modifiers_formset = formset_factory(ModifierForm, extra=0)(prefix="modifiers")
    params_formset = formset_factory(ParameterForm, extra=0)(prefix="parameters")
    sys_field_text_formset = formset_factory(SystemFieldTextForm, extra=0)(prefix="sys_field_text")
    sys_field_weapon_formset = formset_factory(SystemFieldWeaponForm, extra=0)(prefix="sys_field_weapon")
    sys_field_roll_formset = formset_factory(SystemFieldRollForm, extra=0)(prefix="sys_field_roll")
    power_form = PowerForm()
    if existing_power:
        pass
    else:
        pass

    # when an existing gift is edited, populate a new blob that describes its state and then simulate vue clicks
    # ala the random power generator.

    context = {
        'power_blob': PowerBlobGenerator().get_json_power_blob(),
        'modifier_formset': modifiers_formset,
        'params_formset': params_formset,
        'power_form': power_form,
        'sys_field_text_formset': sys_field_text_formset,
        'sys_field_weapon_formset': sys_field_weapon_formset,
        'sys_field_roll_formset': sys_field_roll_formset,
    }
    return context

def create_new_power(request):
    modifier_formset = formset_factory(ModifierForm, extra=0)(request.POST, prefix="modifiers")
    if modifier_formset.is_valid():
        print("MODIFIERS FORMSET VALID")
        # print(modifier_formset.cleaned_data)
    else:
        print("invalid!!")
        # print(modifier_formset.errors)
    power_form = PowerForm(request.POST)
    if power_form.is_valid():
        print("POWER FORM VALID")
        print(power_form.cleaned_data)
    else:
        print("POWER FORM INVALID")
        print(power_form.errors)
    params_formset = formset_factory(ParameterForm, extra=0)(request.POST, prefix="parameters")
    if params_formset.is_valid():
        print("PARAMS VALID")
        print(params_formset.cleaned_data)
    else:
        print("PARAMS INVALID")
        print(params_formset.errors)
        for form in params_formset:
            print(form.errors)
    sys_field_text_formset = formset_factory(SystemFieldTextForm, extra=0)(request.POST, prefix="sys_field_text")
    if sys_field_text_formset.is_valid():
        print("SYS FIELD TEXT VALID")
        print(sys_field_text_formset.cleaned_data)
    else:
        print("SYS FIELD TEXT INVALID")
        print(sys_field_text_formset.errors)
    sys_field_weapon_formset = formset_factory(SystemFieldWeaponForm, extra=0)(request.POST, prefix="sys_field_weapon")
    if sys_field_weapon_formset.is_valid():
        print("weapon field valid")
        print(sys_field_weapon_formset.cleaned_data)
    else:
        print("weapon field INVALID")
        print(sys_field_weapon_formset.errors)
        for form in sys_field_weapon_formset:
            print(form.errors)
    sys_field_roll_formset = formset_factory(SystemFieldRollForm, extra=0)(request.POST, prefix="sys_field_roll")
    if sys_field_roll_formset.is_valid():
        print("roll formset valid")
        print(sys_field_roll_formset.cleaned_data)
    else:
        print("roll fomrset INVALID")
        print(sys_field_roll_formset.errors)
        for form in sys_field_roll_formset:
            print(form.errors)

    # validate forms
    #   Using power blob
    # build new Power
    #   create new system
    #   render system text
    #   creation reason text (can reuse _get_power_creation_reason and _get_power_creation_reason_expanded_text and associated methods)
