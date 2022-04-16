from .models import CREATION_NEW, CREATION_REVISION, CREATION_ADJUSTMENT, CREATION_IMPROVEMENT, CREATION_MAJOR_REVISION, CREATION_UPGRADE_TO_PS2, BODY_, MIND_, PARRY_, SYS_PS2, SYS_LEGACY_POWERS
from django.shortcuts import get_object_or_404
from characters.models import Roll, Attribute, Ability, NO_PARRY_INFO, REACTION, THROWN


def get_roll_from_form_and_system(form, system_field):
    attr = form.cleaned_data["attribute_roll"]
    difficulty = 6
    if system_field.difficulty:
        difficulty = system_field.difficulty
    if attr == BODY_[0] or attr == MIND_[0] or attr == PARRY_[0]:
        if attr == BODY_[0]:
            return Roll.get_body_roll(difficulty=difficulty)
        elif attr == MIND_[0]:
            return Roll.get_mind_roll(difficulty=difficulty)
        elif attr == PARRY_[0]:
            return Roll.get_roll(difficulty=difficulty, parry_type=system_field.parry_type, speed=REACTION)
        else:
            raise ValueError("Unexpected attr")
    else:
        attribute = get_object_or_404(Attribute, id=attr)
        ability = get_object_or_404(Ability, id=form.cleaned_data["ability_roll"])
        return Roll.get_roll(attribute = attribute,
                             ability = ability,
                             difficulty = difficulty,
                             speed=system_field.speed)


def get_power_creation_reason(new_power, old_power):
    if old_power is None:
        return CREATION_NEW
    if new_power.dice_system == SYS_PS2 and old_power.dice_system == SYS_LEGACY_POWERS:
        return CREATION_UPGRADE_TO_PS2

    new_points = new_power.get_gift_cost()
    old_points = old_power.get_gift_cost()
    if new_points > old_points:
        return CREATION_IMPROVEMENT

    if new_points < old_points \
            or _get_changed_components(new_power, old_power) \
            or _get_param_difference_text(new_power, old_power) \
            or _get_added_enhancements(new_power, old_power) \
            or _get_removed_enhancements(new_power, old_power) \
            or _get_added_drawbacks(new_power, old_power) \
            or _get_removed_drawbacks(new_power, old_power):
        return CREATION_REVISION
    return CREATION_ADJUSTMENT


def get_power_creation_reason_expanded_text(new_power, old_power):
    edit_text = ""
    if new_power.creation_reason == CREATION_UPGRADE_TO_PS2:
        edit_text = "Upgraded from old powers system"
    if new_power.creation_reason == CREATION_ADJUSTMENT:
        edit_text = "Text field change"
    if new_power.creation_reason in [CREATION_REVISION, CREATION_IMPROVEMENT, CREATION_MAJOR_REVISION]:
        added_enhancements = _get_added_enhancements(new_power, old_power)
        if len(added_enhancements) > 0:
            edit_text = edit_text + "Added Enhancement"
            if len(added_enhancements) > 1:
                edit_text = edit_text + "s"
            edit_text = edit_text + ": "
            for enhancement in added_enhancements:
                edit_text = edit_text + enhancement.relevant_enhancement.name + ", "

        removed_enhancements = _get_removed_enhancements(new_power, old_power)
        if len(removed_enhancements) > 0:
            edit_text = edit_text + "Removed Enhancement"
            if len(removed_enhancements) > 1:
                edit_text = edit_text + "s"
            edit_text = edit_text + ": "
            for enhancement in removed_enhancements:
                edit_text = edit_text + enhancement.relevant_enhancement.name + ", "

        added_drawbacks = _get_added_drawbacks(new_power, old_power)
        if len(added_drawbacks) > 0:
            edit_text = edit_text + "Added Drawback"
            if len(added_drawbacks) > 1:
                edit_text = edit_text + "s"
            edit_text = edit_text + ": "
            for drawback in added_drawbacks:
                edit_text = edit_text + drawback.relevant_drawback.name + ", "

        removed_drawbacks = _get_removed_drawbacks(new_power, old_power)
        if len(removed_drawbacks) > 0:
            edit_text = edit_text + "Removed Drawback"
            if len(removed_drawbacks) > 1:
                edit_text = edit_text + "s"
            edit_text = edit_text + ": "
            for drawback in removed_drawbacks:
                edit_text = edit_text + drawback.relevant_drawback.name + ", "
        edit_text = edit_text + _get_param_difference_text(new_power, old_power)

    #stopgap bugfix measure until we fix the _get_added_enhancements method by properly using form fields.
    if len(edit_text) < 3:
        edit_text = "Power Adjustment"

    if edit_text[-2] == ',':
        edit_text = edit_text[:-2]
    return edit_text[:1500]


def _get_changed_components(new_power, old_power):
    if new_power.dice_system == SYS_PS2 and old_power.dice_system == SYS_PS2:
        return (new_power.base != old_power.base) \
               or (new_power.vector != old_power.vector) \
               or (new_power.modality != old_power.modality)
    else:
        return False


def _get_added_enhancements(new_power, old_power):
    added_enhancements = []
    for new_enhancement in new_power.enhancement_instance_set.all():
        in_old = False
        for old_enhancement in old_power.enhancement_instance_set.all():
            if old_enhancement.relevant_enhancement.slug == new_enhancement.relevant_enhancement.slug:
                in_old = True
        if not in_old:
            added_enhancements.append(new_enhancement)
    return added_enhancements


def _get_removed_enhancements(new_power, old_power):
    removed_enhancements = []
    for old_enhancement in old_power.enhancement_instance_set.all():
        in_new = False
        for new_enhancement in new_power.enhancement_instance_set.all():
            if old_enhancement.relevant_enhancement.slug == new_enhancement.relevant_enhancement.slug:
                in_new = True
        if not in_new:
            removed_enhancements.append(old_enhancement)
    return removed_enhancements


def _get_added_drawbacks(new_power, old_power):
    added_drawbacks = []
    for new_drawback in new_power.drawback_instance_set.all():
        in_old = False
        for old_drawback in old_power.drawback_instance_set.all():
            if old_drawback.relevant_drawback.slug == new_drawback.relevant_drawback.slug:
                in_old = True
        if not in_old:
            added_drawbacks.append(new_drawback)
    return added_drawbacks


def _get_removed_drawbacks(new_power, old_power):
    removed_drawbacks = []
    for old_drawback in old_power.drawback_instance_set.all():
        in_new = False
        for new_drawback in new_power.drawback_instance_set.all():
            if old_drawback.relevant_drawback.slug == new_drawback.relevant_drawback.slug:
                in_new = True
        if not in_new:
            removed_drawbacks.append(old_drawback)
    return removed_drawbacks


def _get_param_difference_text(new_power, old_power):
    param_text = ""
    param_counter = 0
    for new_param_value in new_power.parameter_value_set.order_by('relevant_power_param_id').all():
        try:
            old_param_value = old_power.parameter_value_set.order_by('relevant_power_param_id').all()[param_counter]
            if old_param_value.value != new_param_value.value:
                param_text = param_text + "Parameter {} changed from {} to {}. "
                param_text = param_text.format(new_param_value.relevant_power_param.relevant_parameter.name, old_param_value.value, new_param_value.value)
        except:
            return "Base Parameters Changed. "
        param_counter = param_counter + 1
    return param_text
