import json, logging
from collections import defaultdict
from django.urls import reverse

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from characters.models import Weapon

from .models import SYS_LEGACY_POWERS, EFFECT, VECTOR, MODALITY, Base_Power, Enhancement, Drawback, Parameter, \
    Base_Power_Category, VectorCostCredit, ADDITIVE, EnhancementGroup, CREATION_NEW, SYS_PS2, Power, Power_Full, \
    Enhancement_Instance, Drawback_Instance, Parameter_Value, Power_Param, SystemFieldText, SystemFieldTextInstance, \
    SystemFieldWeapon, SystemFieldWeaponInstance, SystemFieldRoll, SystemFieldRollInstance
from .formsPs2 import PowerForm, get_modifiers_formset,get_params_formset, get_sys_field_text_formset,\
    get_sys_field_weapon_formset, get_sys_field_roll_formset
from .powerDifferenceUtils import get_roll_from_form_and_system, get_power_creation_reason, \
    get_power_creation_reason_expanded_text

logger = logging.getLogger("app." + __name__)

# TODO: rename to PS2Engine or something
class PowerBlob:

    def __init__(self):
        # TODO: cache this for internal accessors and upload to media file for remote call.
        self.blob = PowerBlob._generate_power_blob()

    def get_json_power_blob(self):
        return json.dumps(self.blob)

    def validate_components(self, effect, vector, modality):
        effect = self.blob["effects"][effect.pk]
        vector = self.blob["vectors"][vector.pk]
        modality = self.blob["modalities"][modality.pk]
        # An Effect is only available on a given modality if it appears in this mapping.
        if not effect["slug"] in self.blob['effects_by_modality'][modality["slug"]]:
            raise ValueError("INVALID GIFT. Modality {} and Effect {} are incompatible".format(modality, effect))

        # A Vector is only available on a given Modality + Effect if it appears in both mappings.
        if not vector["slug"] in self.blob['vectors_by_effect'][effect["slug"]]:
            raise ValueError("INVALID GIFT. Vector {} and Effect {} are incompatible".format(vector, effect))
        if not vector["slug"] in self.blob['vectors_by_modality'][modality["slug"]]:
            raise ValueError("INVALID GIFT. Vector {} and Modality {} are incompatible".format(vector, modality))

    def validate_new_mod_forms(self, effect, vector, modality, modifier_forms):
        # Currently validates details text, modifier multiplicity count, and blacklist/component availability
        # TODO: validate required enhancements and drawbacks
        # TODO: validate mutual exclusivity (or maybe do this in system text rendering?)
        # TODO: validate min num required enhancements and drawbacks
        components = self._components_from_model(effect, vector, modality)
        allowed_enhancement_slugs = PowerBlob._get_allowed_modifiers_for_components(components, "enhancements")
        allowed_drawback_slugs = PowerBlob._get_allowed_modifiers_for_components(components, "drawbacks")
        enhancements = self.blob["enhancements"]
        drawbacks = self.blob["drawbacks"]
        new_enhancement_count_by_slug = {}
        new_drawback_count_by_slug = {}

        for form in modifier_forms:
            mod_slug = form.cleaned_data["mod_slug"]
            if form.cleaned_data["is_enhancement"]:
                modifier = enhancements[mod_slug]
                if mod_slug not in allowed_enhancement_slugs:
                    raise ValueError("Enhancement not allowed: {}. Allowed enhancement slugs:".format(
                        form.cleaned_data,
                        allowed_enhancement_slugs))
                count = new_enhancement_count_by_slug[mod_slug] if mod_slug in new_enhancement_count_by_slug else 0
                new_enhancement_count_by_slug[mod_slug] = count
            else:
                modifier = drawbacks[mod_slug]
                if mod_slug not in allowed_drawback_slugs:
                    raise ValueError("Drawback not allowed: {}. Allowed drawback slugs:".format(
                        form.cleaned_data,
                        allowed_drawback_slugs))
                count = new_drawback_count_by_slug[mod_slug] if mod_slug in new_drawback_count_by_slug else 0
                new_drawback_count_by_slug[mod_slug] = count

            # modifier details validation
            if modifier["detail_field_label"] and "details" not in form.cleaned_data:
                raise ValueError("Modifier must have details text submitted. Mod: {}, Form data: {}".format(
                    modifier,
                    form.cleaned_data))

            # modififier multiplicity validation
            if count > 1 and not modifier["multiplicity_allowed"]:
                raise ValueError("Multiple modifiers but multiplicity not allowed. Mod: {}, Form data: {}".format(
                    modifier,
                    form.cleaned_data))
            if count > 4:
                raise ValueError("More than 4 modifiers with multiplicity found. Mod: {}, Form data: {}".format(
                    modifier,
                    form.cleaned_data))

    def validate_new_param_forms(self, model_effect, model_vector, model_modality, param_formset):
        components = self._components_from_model(model_effect, model_vector, model_modality)
        allowed_power_params = PowerBlob._get_allowed_params_for_components(components)
        allowed_power_param_by_slug = {x["id"]: x for x in allowed_power_params}
        for form in param_formset:
            form_param_id = form.cleaned_data["power_param_id"]
            if form_param_id not in allowed_power_param_by_slug:
                raise ValueError("Power Param not available for components. components: {}, Form data: {}, allowed: {}".format(
                    components,
                    form.cleaned_data,
                    allowed_power_param_by_slug))
            power_param = allowed_power_param_by_slug[form_param_id]
            form_level = form.cleaned_data["level"]
            if form_level < 0 or form_level >= len(power_param["levels"]):
                raise ValueError("Invalid level for power param: {} level {}".format(
                    power_param,
                    form_level))
            allowed_power_param_by_slug.pop(form_param_id)

        if len(allowed_power_param_by_slug) > 0:
            raise ValueError("parameter not submitted in form: {}".format(allowed_power_param_by_slug))

    def validate_new_field_forms(self, model_effect, model_vector, model_modality, text_forms, weap_forms, roll_forms):
        components = self._components_from_model(model_effect, model_vector, model_modality)
        text_field_ids = set()
        weapon_field_ids = set()
        roll_field_ids = set()
        for component in components:
            if "text_fields" in component:
                text_field_ids.update(set([x["id"] for x in component["text_fields"]]))
            if "weapon_fields" in component:
                weapon_field_ids.update(set([x["id"] for x in component["weapon_fields"]]))
            if "roll_fields" in component:
                roll_field_ids.update(set([x["id"] for x in component["roll_fields"]]))
        for form in text_forms:
            field_id = form.cleaned_data["field_id"]
            if field_id not in text_field_ids:
                raise ValueError("field not expected: {}".format(form.cleaned_data))
        for form in weap_forms:
            field_id = form.cleaned_data["field_id"]
            if field_id not in weapon_field_ids:
                raise ValueError("field not expected: {}".format(form.cleaned_data))
        for form in roll_forms:
            field_id = form.cleaned_data["field_id"]
            if field_id not in roll_field_ids:
                raise ValueError("field not expected: {}".format(form.cleaned_data))

    @staticmethod
    def _get_allowed_params_for_components(components):
        params = []
        for component in components:
            params.extend(component["parameters"])
        return params

    @staticmethod
    def _get_allowed_modifiers_for_components(components, modifier_type):
        blacklisted_mod_slugs = set()
        selected_mod_slugs = set()
        for component in components:
            blacklisted_mod_slugs.update(set([mod_slug for mod_slug in component["blacklist_" + modifier_type]]))
            selected_mod_slugs.update(set([mod_slug for mod_slug in component[modifier_type]]))
        allowed_modifiers = selected_mod_slugs.difference(blacklisted_mod_slugs)
        return allowed_modifiers

    @staticmethod
    def _generate_power_blob():
        vectors = PowerBlob._generate_component_blob(VECTOR)
        effects = PowerBlob._generate_component_blob(EFFECT)
        modalities = PowerBlob._generate_component_blob(MODALITY)
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
            'enhancements': PowerBlob._generate_modifier_blob(Enhancement),
            'drawbacks': PowerBlob._generate_modifier_blob(Drawback),

            # The parameters dictionary only contains the parameter's name and substitution.
            # The level info is on the gift components
            'parameters': PowerBlob._generate_param_blob(),

            'component_categories': PowerBlob._generate_component_category_blob(),

            # An Effect is only available on a given modality if it appears in this mapping.
            'effects_by_modality': effects_by_modality,

            # A Vector is only available on a given Modality + Effect if it appears in both mappings.
            'vectors_by_effect': vectors_by_effect,
            'vectors_by_modality': vectors_by_modality,

            'effect_vector_gift_credit': PowerBlob._generate_effect_vector_gift_credits_blob(),

            # Weapon choice system fields use a Weapon's pk as the non-display value. Stats in this blob by pk.
            'weapon_replacements_by_pk': PowerBlob._generate_weapons_blob(),

            'enhancement_group_by_pk': PowerBlob._generate_enhancement_groups_blob()
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
        return {x.pk: PowerBlob._replacements_from_weapon(x) for x in weapons}

    @staticmethod
    def _replacements_from_weapon(weapon):
        return [
            PowerBlob._replacement("selected-weapon-name", weapon.name),
            PowerBlob._replacement("selected-weapon-type", weapon.get_type_display()),
            PowerBlob._replacement("selected-weapon-attack-roll", weapon.attack_roll_replacement()),
            PowerBlob._replacement("selected-weapon-damage", str(weapon.bonus_damage)),
            PowerBlob._replacement("selected-weapon-range", weapon.range),
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

    def _components_from_model(self, effect, vector, modality):
        effect = self.blob["effects"][effect.pk]
        vector = self.blob["vectors"][vector.pk]
        modality = self.blob["modalities"][modality.pk]
        components = [effect, vector, modality]
        return components


def get_edit_context(existing_power_full=None, is_edit=False):
    modifiers_formset = get_modifiers_formset()
    params_formset = get_params_formset()
    sys_field_text_formset = get_sys_field_text_formset()
    sys_field_weapon_formset = get_sys_field_weapon_formset()
    sys_field_roll_formset = get_sys_field_roll_formset()
    power_form = PowerForm()
    context = {
        'power_blob': PowerBlob().get_json_power_blob(),
        'modifier_formset': modifiers_formset,
        'params_formset': params_formset,
        'power_form': power_form,
        'sys_field_text_formset': sys_field_text_formset,
        'sys_field_weapon_formset': sys_field_weapon_formset,
        'sys_field_roll_formset': sys_field_roll_formset,
    }
    form_url = reverse("powers:powers_create_ps2")
    if existing_power_full:
        context['power_edit_blob'] = json.dumps(existing_power_full.latest_revision().to_edit_blob())
    if is_edit:
        form_url = reverse("powers:powers_edit_ps2", kwargs={"power_full_id": existing_power_full.pk})
    context["form_url"] = form_url
    return context


# TODO: permissions are checked before this method is called.
def save_gift(request, power_full=None, character=None):
    if not request.POST:
        raise ValueError("Can only create new gift from post request")
    power_form = PowerForm(request.POST)
    if power_form.is_valid():
        new_power = _create_new_power_and_save(power_form=power_form, request=request)
        _populate_power_change_log(new_power, power_full)
        if not power_full:
            # brand new Gift
            new_power.creation_reason = CREATION_NEW
            new_power.creation_reason_expanded_text = "Initial power creation"
            power_full = _create_new_power_full(power_form, new_power, character)
            if request.user.id:
                power_full.owner = request.user
        power_full.save()
        if request.user.is_superuser:
            power_full.tags.set(power_form.cleaned_data["tags"])
            power_full.example_description = power_form.cleaned_data["example_description"]
        power_full.latest_rev = new_power
        power_full.save()
        new_power.parent_power = power_full
        new_power.save()
        if character:
            character.reset_attribute_bonuses()
        return new_power
    else:
        logger.error("Invalid Power form. errors: {}".format(power_form.errors))
        raise ValueError("Invalid Power form!")


def _populate_power_system_and_errata(power_blob, power, modifier_instances, param_instances, field_instances):
    # TODO: do the system text rendering even though it's annoying and hard.
    power.system = "Server-side system text rendering incoming"
    power.errata = "Server-side errata text rendering incoming"


def _create_new_power_and_save(power_form, request):
    power_blob = PowerBlob()

    # power is not saved yet
    power = _get_power_from_form_and_validate(power_form=power_form, power_blob=power_blob, user=request.user)

    # These instances are unsaved and do not yet reference the power.
    modifier_instances = _get_modifier_instances_and_validate(
        request.POST, power_blob, power.base, power.vector, power.modality)
    param_instances = _get_param_instances_and_validate(
        request.POST, power_blob, power.base, power.vector, power.modality)
    field_instances = _get_field_instances_and_validate(
        request.POST, power_blob, power.base, power.vector, power.modality)
    _populate_power_system_and_errata(power_blob, power, modifier_instances, param_instances, field_instances)

    # At this point, we can be sure the power is valid, so we save everything to the DB and hook up our instances.
    power.save()
    for mod in modifier_instances:
        mod.relevant_power = power
        mod.save()
    for param in param_instances:
        param.relevant_power = power
        param.save()
    for field in field_instances:
        field.relevant_power = power
        field.save()
    return power


def _get_power_from_form_and_validate(power_form, power_blob, user=None):
    power = Power(name=power_form.cleaned_data['name'],
                  flavor_text=power_form.cleaned_data['tagline'],
                  description=power_form.cleaned_data['description'],
                  base=power_form.cleaned_data["effect"],
                  vector=power_form.cleaned_data["vector"],
                  modality=power_form.cleaned_data["modality"],
                  dice_system=SYS_PS2)
    if user and user.id:
        power.created_by = user
    power_blob.validate_components(power.base, power.vector, power.modality)
    return power


def _get_modifier_instances_and_validate(POST, power_blob, effect, vector, modality):
    modifiers_formset = get_modifiers_formset(POST)
    if modifiers_formset.is_valid():
        selected_modifier_forms = [x for x in modifiers_formset if "is_selected" in x.cleaned_data and x.cleaned_data["is_selected"]]
        power_blob.validate_new_mod_forms(effect, vector, modality, selected_modifier_forms)
        modifiers = []
        for form in selected_modifier_forms:
            details = form.cleaned_data["details"] if "details" in form.cleaned_data else None
            if form.cleaned_data["is_enhancement"]:
                enhancement = get_object_or_404(Enhancement, pk=form.cleaned_data["mod_slug"])
                new_instance = Enhancement_Instance(relevant_enhancement=enhancement, detail=details)
                modifiers.append(new_instance)
            else:
                drawback = get_object_or_404(Drawback, pk=form.cleaned_data["mod_slug"])
                new_instance = Drawback_Instance(relevant_drawback=drawback, detail=details)
                modifiers.append(new_instance)
        return modifiers
    else:
        logger.error("Invalid modifier form. errors: {}".format(modifiers_formset.errors))
        raise ValueError("Invalid modifiers formset!")


def _get_param_instances_and_validate(POST, power_blob, effect, vector, modality):
    params_formset = get_params_formset(POST)
    if params_formset.is_valid():
        power_blob.validate_new_param_forms(effect, vector, modality, params_formset)
        params = []
        for form in params_formset:
            power_param = get_object_or_404(Power_Param, pk=form.cleaned_data["power_param_id"])
            param_val = Parameter_Value(relevant_power_param=power_param,
                                        value=form.cleaned_data["level"])
            params.append(param_val)
        return params
    else:
        logger.error("Invalid param form. errors: {}".format(params_formset.errors))
        raise ValueError("Invalid param formset!")


def _get_field_text_instances(sys_field_text_formset):
    instances = []
    for form in sys_field_text_formset:
        system_field = get_object_or_404(SystemFieldText, id=form.cleaned_data["field_id"])
        field_instance = SystemFieldTextInstance(relevant_field=system_field, value=form.cleaned_data["detail_text"])
        instances.append(field_instance)
    return instances


def _get_field_weapon_instances(sys_field_weapon_formset):
    instances = []
    for form in sys_field_weapon_formset:
        system_field = get_object_or_404(SystemFieldWeapon, id=form.cleaned_data["field_id"])
        field_instance = SystemFieldWeaponInstance(relevant_field=system_field, weapon=form.cleaned_data["weapon_choice"])
        instances.append(field_instance)
    return instances


def _get_field_roll_instances(sys_field_roll_formset):
    instances = []
    for form in sys_field_roll_formset:
        system_field = get_object_or_404(SystemFieldRoll, id=form.cleaned_data["field_id"])
        roll = get_roll_from_form_and_system(form, system_field)
        field_instance = SystemFieldRollInstance(relevant_field=system_field, roll=roll)
        instances.append(field_instance)
    return instances


def _get_field_instances_and_validate(POST, power_blob, effect, vector, modality):
    sys_field_text_formset = get_sys_field_text_formset(POST)
    sys_field_weapon_formset = get_sys_field_weapon_formset(POST)
    sys_field_roll_formset = get_sys_field_roll_formset(POST)
    if sys_field_text_formset.is_valid() and sys_field_weapon_formset.is_valid() and sys_field_roll_formset.is_valid():
        power_blob.validate_new_field_forms(
            effect, vector, modality, sys_field_text_formset, sys_field_weapon_formset, sys_field_roll_formset)
        field_instances = []
        field_instances.extend(_get_field_text_instances(sys_field_text_formset))
        field_instances.extend(_get_field_weapon_instances(sys_field_weapon_formset))
        field_instances.extend(_get_field_roll_instances(sys_field_roll_formset))
        return field_instances
    else:
        logger.error("Invalid sys field formset. text errors: {}, weapon errors: {}, roll errors: {}".format(
            sys_field_text_formset.errors,
            sys_field_weapon_formset.errors,
            sys_field_roll_formset.errors))
        raise ValueError("Invalid sys field formset!")


def _populate_power_change_log(new_power, power_full):
    if power_full:
        new_power.creation_reason = get_power_creation_reason(new_power, power_full.latest_revision())
        new_power.creation_reason_expanded_text = get_power_creation_reason_expanded_text(
            new_power, power_full.latest_revision())
    else:
        # new gift
        new_power.creation_reason = CREATION_NEW
        new_power.creation_reason_expanded_text = "Initial power creation"


def _create_new_power_full(power_form, new_power, character=None):
    new_power_full = Power_Full(
        name=power_form.cleaned_data['name'],
        dice_system=SYS_PS2,
        base=new_power.base)
    if character:
        new_power_full.private = character.private
        new_power_full.character = character
    return new_power_full

