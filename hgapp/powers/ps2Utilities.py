import json, logging
from django.urls import reverse

from django.shortcuts import get_object_or_404

from characters.models import Artifact

from .models import SYS_LEGACY_POWERS, EFFECT, VECTOR, MODALITY, Base_Power, Enhancement, Drawback, Parameter, \
    Base_Power_Category, VectorCostCredit, ADDITIVE, EnhancementGroup, CREATION_NEW, SYS_PS2, Power, Power_Full, \
    Enhancement_Instance, Drawback_Instance, Parameter_Value, Power_Param, SystemFieldText, SystemFieldTextInstance, \
    SystemFieldWeapon, SystemFieldWeaponInstance, SystemFieldRoll, SystemFieldRollInstance, PowerSystem, \
    CRAFTING_SIGNATURE
from .formsPs2 import PowerForm, get_modifiers_formset, get_params_formset, get_sys_field_text_formset, \
    get_sys_field_weapon_formset, get_sys_field_roll_formset, make_select_signature_artifact_form
from .powerDifferenceUtils import get_roll_from_form_and_system, get_power_creation_reason, \
    get_power_creation_reason_expanded_text
from .Ps2Engine import PowerEngine, SystemTextRenderer

logger = logging.getLogger("app." + __name__)


def get_edit_context(existing_power_full=None, is_edit=False, existing_char=None):
    modifiers_formset = get_modifiers_formset()
    params_formset = get_params_formset()
    sys_field_text_formset = get_sys_field_text_formset()
    sys_field_weapon_formset = get_sys_field_weapon_formset()
    sys_field_roll_formset = get_sys_field_roll_formset()
    power_form = PowerForm()
    sig_item_artifact_form = make_select_signature_artifact_form(
        existing_character=existing_char,
        existing_power=existing_power_full)()
    categories = Base_Power_Category.objects.all()
    context = {
        'power_blob_url': PowerSystem.get_singleton().get_json_url(),
        'character_blob': existing_char.to_create_power_blob() if existing_char else None,
        'modifier_formset': modifiers_formset,
        'params_formset': params_formset,
        'power_form': power_form,
        'sig_item_artifact_form': sig_item_artifact_form,
        'sys_field_text_formset': sys_field_text_formset,
        'sys_field_weapon_formset': sys_field_weapon_formset,
        'sys_field_roll_formset': sys_field_roll_formset,
        'cat_colors': [(cat.container_class(), cat.color) for cat in categories],
    }
    form_url = reverse("powers:powers_create_ps2")
    if existing_power_full:
        context['power_edit_blob'] = json.dumps(existing_power_full.latest_revision().to_edit_blob())
    if is_edit:
        form_url = reverse("powers:powers_edit_ps2", kwargs={"power_full_id": existing_power_full.pk})
    elif existing_char:
        form_url = reverse("powers:powers_create_ps2_for_char", kwargs={"character_id": existing_char.pk})
    context["form_url"] = form_url
    return context


# TODO: permissions are checked before this method is called.
def save_gift(request, power_full=None, character=None):
    if not request.POST:
        raise ValueError("Can only create new gift from post request")
    power_form = PowerForm(request.POST)
    if power_form.is_valid():
        SignatureArtifactForm = make_select_signature_artifact_form(
            existing_character=character,
            existing_power=power_full)
        new_power = _create_new_power_and_save(power_form=power_form, request=request, SigArtifactForm=SignatureArtifactForm)
        _populate_power_change_log(new_power, power_full)

        if not power_full:
            # brand new Gift
            new_power.creation_reason = CREATION_NEW
            new_power.creation_reason_expanded_text = "Initial power creation"
            power_full = _create_new_power_full(power_form, new_power, character)
            if request.user.id:
                power_full.owner = request.user
            power_full.save()
            previous_rev = None
        else:
            previous_rev = power_full.latest_rev
            power_full.crafting_type = new_power.modality.crafting_type
        _handle_sig_artifact(request, SignatureArtifactForm, power_full, new_power, previous_rev)
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


def _populate_power_system_and_errata(power_engine, power, modifier_instances, param_instances, field_instances):
    renderer = SystemTextRenderer(power_engine)
    renderer.populate_rendered_fields(power, modifier_instances, param_instances, field_instances)


def _calculate_req_status(power_engine, power, modifier_instances, param_instances):
    return power_engine.calculate_req_status(power.base_id,
                                             power.vector_id,
                                             power.modality_id,
                                             modifier_instances,
                                             param_instances)


def _create_new_power_and_save(power_form, request, SigArtifactForm):
    power_engine = PowerEngine()

    # power is not saved yet
    power = _get_power_from_form_and_validate(power_form=power_form, power_engine=power_engine, user=request.user)

    if power.modality.crafting_type == CRAFTING_SIGNATURE:
        sig_artifact_form = SigArtifactForm(request.POST)
        # do nothing with the form yet, just check its validity so we know whether we should save the power or not.
        if not sig_artifact_form.is_valid():
            raise ValueError("Invalid signature artifact form")

    # These instances are unsaved and do not yet reference the power.
    modifier_instances = _get_modifier_instances_and_validate(
        request.POST, power_engine, power.base_id, power.vector_id, power.modality_id)
    param_instances = _get_param_instances_and_validate(
        request.POST, power_engine, power.base_id, power.vector_id, power.modality_id)
    field_instances = _get_field_instances_and_validate(
        request.POST, power_engine, power.base_id, power.vector_id, power.modality_id)
    _populate_power_system_and_errata(power_engine, power, modifier_instances, param_instances, field_instances)

    power.enhancement_names = [enh.relevant_enhancement.name for enh in modifier_instances if hasattr(enh, "relevant_enhancement")]
    power.drawback_names = [mod.relevant_drawback.name for mod in modifier_instances if hasattr(mod, "relevant_drawback")]
    power.shouldDisplayVector = power_engine.should_display_vector(power.base_id, power.modality_id)
    power.required_status = _calculate_req_status(power_engine, power, modifier_instances, param_instances)
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


def _get_power_from_form_and_validate(power_form, power_engine, user=None):
    power = Power(name=power_form.cleaned_data['name'],
                  flavor_text=power_form.cleaned_data['tagline'],
                  description=power_form.cleaned_data['description'],
                  extended_description=power_form.cleaned_data['extended_description'],
                  base=power_form.cleaned_data["effect"],
                  vector=power_form.cleaned_data["vector"],
                  modality=power_form.cleaned_data["modality"],
                  dice_system=SYS_PS2)
    if user and user.id:
        power.created_by = user
    power_engine.validate_components(power.base_id, power.vector_id, power.modality_id)
    return power


def _get_modifier_instances_and_validate(POST, power_engine, effect_id, vector_id, modality_id):
    modifiers_formset = get_modifiers_formset(POST)
    if modifiers_formset.is_valid():
        selected_modifier_forms = [x for x in modifiers_formset if "is_selected" in x.cleaned_data and x.cleaned_data["is_selected"]]
        power_engine.validate_new_mod_forms(effect_id, vector_id, modality_id, selected_modifier_forms)
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


def _get_param_instances_and_validate(POST, power_engine, effect_id, vector_id, modality_id):
    params_formset = get_params_formset(POST)
    if params_formset.is_valid():
        power_engine.validate_new_param_forms(effect_id, vector_id, modality_id, params_formset)
        params = []
        for form in params_formset:
            if not form.cleaned_data["level"]:
                # Disabled param
                continue
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


def _get_field_instances_and_validate(POST, power_engine, effect_id, vector_id, modality_id):
    sys_field_text_formset = get_sys_field_text_formset(POST)
    sys_field_weapon_formset = get_sys_field_weapon_formset(POST)
    sys_field_roll_formset = get_sys_field_roll_formset(POST)
    if sys_field_text_formset.is_valid() and sys_field_weapon_formset.is_valid() and sys_field_roll_formset.is_valid():
        power_engine.validate_new_field_forms(
            effect_id, vector_id, modality_id, sys_field_text_formset, sys_field_weapon_formset, sys_field_roll_formset)
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
        base=new_power.base,
        crafting_type=power_form.cleaned_data["modality"].crafting_type)
    if character:
        new_power_full.private = character.private
        new_power_full.character = character
    return new_power_full


def _handle_sig_artifact(request, SignatureArtifactForm, power_full, new_power, previous_rev=None):
    # First get the new artifact if there is one
    sig_artifact_form = SignatureArtifactForm(request.POST)
    if new_power.modality.crafting_type == CRAFTING_SIGNATURE:
        new_artifact = sig_artifact_form.cleaned_data["selected_artifact"]
        if not new_artifact:
            new_artifact = Artifact.create(
                name=power_full.name,
                description=".",
                crafting_character=power_full.character,
                creating_player=request.user,
                is_signature=True,
            )
    else:
        new_artifact = None

    # Now update relations
    if previous_rev:
        if previous_rev.modality.crafting_type == CRAFTING_SIGNATURE:
            old_artifact = previous_rev.artifacts_set.filter(is_signature=True).get()
            previous_rev.artifacts.remove(old_artifact) # unlink old rev from old artifact
            if old_artifact != new_artifact or new_power.modality.crafting_type != CRAFTING_SIGNATURE:
                power_full.artifacts.remove(old_artifact) # unlink power_full from old artifact
                if old_artifact.power_full_set.filter(crafting_type=CRAFTING_SIGNATURE).count() == 0:
                    old_artifact.delete()
    if new_power.modality.crafting_type == CRAFTING_SIGNATURE:
        new_power.artifacts.add(new_artifact) # link new rev with artifact
        power_full.artifacts.add(new_artifact) # it's okay to duplicitively add to a django many-to-many


