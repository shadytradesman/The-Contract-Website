from django.forms import formset_factory
from django.utils import timezone
from django.shortcuts import get_object_or_404
import bleach
import json

from .forms import CreatePowerForm, make_enhancement_form, make_drawback_form, make_parameter_form, \
    SystemFieldRollForm, SystemFieldTextForm
from .models import Enhancement_Instance, Drawback_Instance, Power, DICE_SYSTEM, Enhancement, Drawback, \
    Power_Param, SystemFieldText, SystemFieldRoll, SystemFieldTextInstance, SystemFieldRollInstance, \
    Parameter_Value, Base_Power_System, Power_Full, CREATION_REASON, PowerTutorial, MIND_, BODY_, PARRY_

from characters.models import Roll, Attribute, Ability, NO_PARRY_INFO, REACTION, THROWN


def get_create_power_context_from_base(base_power, character=None):
    system = base_power.get_system()
    primary_form = CreatePowerForm(base_power, initial={'system': system.system_text})
    enhancement_forms = []
    for enhancement in Enhancement.objects.filter(pk__in=base_power.enhancements.all()):
        enhancement_forms.append(formset_factory(make_enhancement_form(enhancement), extra = 1)())
    drawback_forms = []
    for drawback in Drawback.objects.filter(pk__in=base_power.drawbacks.all()):
        drawback_forms.append(formset_factory(make_drawback_form(drawback), extra = 1)())
    parameter_forms = []
    for parameter in Power_Param.objects.filter(relevant_base_power=base_power).all():
        parameter_forms.append(formset_factory(make_parameter_form(parameter))())
    roll_fields_formset = _get_system_roll_field_formset(system)
    text_fields_formset = _get_system_text_field_formset(system)
    system = Base_Power_System.objects.filter(dice_system=DICE_SYSTEM[1][0]).get(base_power=base_power.slug)
    requirements = _get_modifier_requirements(Enhancement.objects.filter(pk__in=base_power.enhancements.all()),
                                             Drawback.objects.filter(pk__in=base_power.drawbacks.all()))
    context = {
        'base_power': base_power,
        'power_system': system,
        'form': primary_form,
        'parameters': parameter_forms,
        'enhancements': enhancement_forms,
        'drawbacks': drawback_forms,
        'requirements_json': json.dumps(requirements),
        'character': character,
        'roll_fields': roll_fields_formset,
        'text_fields': text_fields_formset,
    }
    if character:
        unspent_rewards = []
        for reward in character.unspent_rewards().all():
            unspent_rewards.append("{} from {}".format(reward.type_text(), reward.reason_text()))
        context["unspent_rewards_json"] = json.dumps(unspent_rewards)
        spent_rewards = []
        context["spent_rewards_json"] = json.dumps(spent_rewards)
    context = _add_tutorial_to_context(context)
    return context


def get_create_power_context_from_power(power, new=True):
    initial = {'system': power.get_system(),
     'description': power.description,
     'flavor': power.flavor_text,
     'power_name': power.name}
    if power.parent_power:
        initial['tags'] = power.parent_power.tags.all()
        initial['example_description'] = power.parent_power.example_description

    system = Base_Power_System.objects.filter(dice_system=DICE_SYSTEM[1][0]).get(base_power=power.base.slug)
    text_fields_formset = _get_text_field_formsets_for_edit(power, system)
    roll_fields_formset = _get_roll_field_formsets_for_edit(power, system)

    primary_form = CreatePowerForm(power.base,
                                   initial=initial)
    enhancement_forms = _get_enhancement_formsets_from_power(power)
    drawback_forms = _get_drawback_formsets_from_power(power)
    parameter_forms = []
    for parameter_value in Parameter_Value.objects.filter(relevant_power=power).all():
        init = [{'level_picker': parameter_value.value}]
        parameter_forms.append(formset_factory(make_parameter_form(parameter_value.relevant_power_param), extra = 0)(initial = init))
    requirements = _get_modifier_requirements(Enhancement.objects.filter(pk__in=power.base.enhancements.all()),
                                             Drawback.objects.filter(pk__in=power.base.drawbacks.all()))
    context = {
        'base_power': power.base,
        'power_system': system,
        'form': primary_form,
        'parameters': parameter_forms,
        'enhancements': enhancement_forms,
        'drawbacks': drawback_forms,
        'requirements_json': json.dumps(requirements),
        'roll_fields': roll_fields_formset,
        'text_fields': text_fields_formset,
    }

    if power.parent_power is not None:
        if power.parent_power.character is not None and new:
            context["character"] = power.parent_power.character
            unspent_rewards = []
            for reward in power.parent_power.character.unspent_rewards().all():
                unspent_rewards.append("{} from {}".format(reward.type_text(), reward.reason_text()))
            context["unspent_rewards_json"] = json.dumps(unspent_rewards)
            spent_rewards = []
            for reward in power.parent_power.reward_list():
                spent_rewards.append("{} from {}".format(reward.type_text(), reward.reason_text()))
            context["spent_rewards_json"] = json.dumps(spent_rewards)
    context = _add_tutorial_to_context(context)
    return context

def _get_text_field_formsets_for_edit(power, system):
    TextFieldsFormset = formset_factory(SystemFieldTextForm, extra=0)
    text_system_fields = system.systemfieldtext_set.order_by("id").all()
    instances = power.systemfieldtextinstance_set.all()
    value_by_field_id = {n.relevant_field.id: n.value for n in instances}
    return TextFieldsFormset(
        initial=[{'system_field_id': x.id,
                  'system_field': x,
                  'field_text': value_by_field_id[x.id] if x.id in value_by_field_id else ""
                  } for x in text_system_fields],
        prefix="system_text_fields")

def _get_roll_field_formsets_for_edit(power, system):
    RollFieldsFormset = formset_factory(SystemFieldRollForm, extra=0)
    roll_system_fields = system.systemfieldroll_set.order_by("id").all()
    instances = power.systemfieldrollinstance_set.all()

    value_by_field_id = {n.relevant_field.id: n.roll for n in instances}
    return RollFieldsFormset(
        initial=[{'system_field_id': x.id,
                  'system_field': x,
                  'ability_roll': _get_roll_initial_ability(value_by_field_id[x.id]) if x.id in value_by_field_id else None,
                  'attribute_roll': _get_roll_initial_attribute(value_by_field_id[x.id]) if x.id in value_by_field_id else None,
                  }
                 for x in roll_system_fields],
        prefix="system_roll_fields")


def _get_roll_initial_ability(roll):
    if roll.ability:
        return roll.ability.id
    else:
        return None


def _get_roll_initial_attribute(roll):
    if roll.attribute:
        return roll.attribute.id
    elif roll.is_mind:
        return MIND_
    elif roll.is_body:
        return BODY_
    elif roll.parry_type != NO_PARRY_INFO:
        return PARRY_
    else:
        raise ValueError("Unknown roll attribute")


def get_edit_power_context_from_power(og_power):
    context = get_create_power_context_from_power(og_power)
    if og_power.parent_power is not None and og_power.parent_power.owner is not None:
        context["owner"] = og_power.parent_power.owner
    context["og_power"] = og_power
    return context


def create_power_for_new_edit(base_power, request, power_full):
    power_form = CreatePowerForm(base_power, request.POST)
    if power_form.is_valid():
        old_power = power_full.latest_revision()
        if request.user.is_superuser:
            power_full.tags.set(power_form.cleaned_data["tags"])
            power_full.example_description = power_form.cleaned_data["example_description"]
            power_full.save()
        new_power = _create_power_from_post_and_base(base_power, request, power_full)
        new_power.creation_reason = _get_power_creation_reason(new_power, old_power)
        new_power.creation_reason_expanded_text = _get_power_creation_reason_expanded_text(new_power, old_power)
        new_power.save()
        if hasattr(power_full, "character") and power_full.character:
            power_full.character.reset_attribute_bonuses()
        return new_power

    
def create_new_power_and_parent(base_power, request, character=None):
    form = CreatePowerForm(base_power, request.POST)
    if form.is_valid():
        power_full = _create_new_full_power(power_form=form, base=base_power)
        if request.user.id:
            power_full.owner = request.user
        if character:
            power_full.character = character
        power_full.save()
        if request.user.is_superuser:
            power_full.tags.set(form.cleaned_data["tags"])
            power_full.example_description = form.cleaned_data["example_description"]
            power_full.save()
        new_power = _create_power_from_post_and_base(base_power, request, power_full)
        new_power.creation_reason = CREATION_REASON[0][0]
        new_power.creation_reason_expanded_text = "Initial power creation"
        new_power.save()
        if character:
            character.reset_attribute_bonuses()
        return new_power
    else:
        print(form.errors)
        return None


def refund_or_assign_rewards(new_power, old_power=None):
    og_point_value = 0
    if old_power:
        og_point_value=old_power.get_point_value()
    delta = new_power.get_point_value() - og_point_value
    if delta == 0:
        return
    if delta > 0:
        if new_power.parent_power.character is not None:
            unspent_gifts = new_power.parent_power.character.unspent_rewards()
            for a in range(delta):
                if a == len(unspent_gifts):
                    break
                unspent_gifts[a].assign_to_power(new_power)
    if delta < 0:
        if new_power.parent_power.character is not None and old_power:
            spent_gifts = old_power.parent_power.reward_list()
            for a in range(delta*-1):
                if a == len(spent_gifts):
                    break
                spent_gifts[a].refund_keeping_character_assignment()


def _get_enhancement_formsets_from_power(power):
    enhancement_forms = []
    enhancement_instances = Enhancement_Instance.objects.filter(relevant_power=power).all()
    for base_enhancement in Enhancement.objects.filter(pk__in=power.base.enhancements.all()):
        instances_of_this_enhancement = set(
            x for x in enhancement_instances if (x.relevant_enhancement == base_enhancement))
        init = []
        num_extra = 0
        for enhancement_instance in instances_of_this_enhancement:
            init.append({
                'is_selected': True,
                'detail_text': enhancement_instance.detail,
            })
        if base_enhancement.multiplicity_allowed or not instances_of_this_enhancement:
            num_extra = 1
        new_form = formset_factory(make_enhancement_form(base_enhancement), extra=num_extra, max_num=4)(initial=init)
        enhancement_forms.append(new_form)
    return enhancement_forms


def _get_drawback_formsets_from_power(power):
    drawback_forms = []
    drawback_instances = Drawback_Instance.objects.filter(relevant_power=power).all()
    for base_drawback in Drawback.objects.filter(pk__in=power.base.drawbacks.all()):
        instances_of_this_drawback = set(
            x for x in drawback_instances if (x.relevant_drawback == base_drawback))
        init = []
        num_extra = 0
        for drawback_instance in instances_of_this_drawback:
            init.append({
                'is_selected': True,
                'detail_text': drawback_instance.detail,
            })
        if base_drawback.multiplicity_allowed or not instances_of_this_drawback:
            num_extra = 1
        new_form = formset_factory(make_drawback_form(base_drawback), extra=num_extra, max_num=4)(initial=init)
        drawback_forms.append(new_form)
    return drawback_forms


def _add_tutorial_to_context(context):
    tutorial = get_object_or_404(PowerTutorial)
    context['modal_header'] = tutorial.modal_edit_header
    context['modal_text'] = tutorial.modal_edit
    context['modal_art'] = 'overrides/art/ocean-walking-copy.jpg'
    return context


def _get_modifier_requirements(enhancements, drawbacks):
    requirements = {}
    for enhancement in enhancements:
        if enhancement.required_Enhancements:
            required = []
            for req_enhancement in enhancement.required_Enhancements.all():
                required.append( req_enhancement.form_name() )
            requirements[enhancement.form_name()] = required
    for drawback in drawbacks:
        if drawback.required_drawbacks:
            required = []
            for req_drawback in drawback.required_drawbacks.all():
                required.append(req_drawback.form_name())
            requirements[drawback.form_name()] = required
    return requirements


def _get_enhancement_instances(post_data, enhancements, new_power):
    instances = []
    for enhancement in enhancements:
        if enhancement.slug + "-e-is_selected" in post_data:
            detail_texts = []
            if enhancement.slug + "-e-detail_text" in post_data:
                detail_texts = post_data.getlist(enhancement.slug + "-e-detail_text")
            for on in post_data.getlist(enhancement.slug + "-e-is_selected"):
                if detail_texts:
                    new_detail_text = bleach.clean(detail_texts.pop(0))
                else:
                    new_detail_text = ""
                instances.append(Enhancement_Instance(relevant_enhancement=enhancement,
                                     relevant_power=new_power,
                                     detail=new_detail_text))
    return instances


def _get_drawback_instances(post_data, drawbacks, new_power):
    instances = []
    for drawback in drawbacks:
        if drawback.slug + "-d-is_selected" in post_data:
            detail_texts = []
            if drawback.slug + "-d-detail_text" in post_data:
                detail_texts = post_data.getlist(drawback.slug + "-d-detail_text")
            for on in post_data.getlist(drawback.slug + "-d-is_selected"):
                if detail_texts:
                    new_detail_text = bleach.clean(detail_texts.pop(0))
                else:
                    new_detail_text = ""
                instances.append(Drawback_Instance(relevant_drawback=drawback,
                                     relevant_power=new_power,
                                     detail=new_detail_text))
    return instances


def _create_new_full_power(power_form, base):
    return Power_Full(name=power_form.cleaned_data['power_name'],
                  dice_system=DICE_SYSTEM[1][0],
                  base=base,
                  pub_date=timezone.now())


def _get_power_from_form(power_form, base):
    return Power(name=power_form.cleaned_data['power_name'],
                  flavor_text=power_form.cleaned_data['flavor'],
                  description=power_form.cleaned_data['description'],
                  system=power_form.cleaned_data['system'],
                  base=base,
                  dice_system=DICE_SYSTEM[1][0],
                  pub_date=timezone.now())


def _get_roll_from_form_and_system(form, system_field):
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


def _create_power_from_post_and_base(base_power, request, power_full):
    form = CreatePowerForm(base_power, request.POST)
    if form.is_valid():
        system = Base_Power_System.objects.filter(dice_system=DICE_SYSTEM[1][0]).get(base_power=base_power.slug)
        power = _get_power_from_form(power_form=form, base=base_power)
        if request.user.id:
            power.created_by = request.user
        power.parent_power = power_full
        power.save()
        enhancement_instances = _get_enhancement_instances(post_data=request.POST,
                                                           enhancements=Enhancement.objects.filter(
                                                              pk__in=base_power.enhancements.all()),
                                                          new_power=power)
        for enhancement_instance in enhancement_instances:
            enhancement_instance.save()
        drawback_instances = _get_drawback_instances(post_data=request.POST,
                                                    drawbacks=Drawback.objects.filter(
                                                        pk__in=base_power.drawbacks.all()),
                                                    new_power=power)
        for drawback_instance in drawback_instances:
            drawback_instance.save()
        for power_param in Power_Param.objects.filter(relevant_base_power=base_power):
            param_val = Parameter_Value(relevant_power=power,
                                        relevant_power_param=power_param,
                                        value=request.POST[power_param.relevant_parameter.slug])
            param_val.save()
        text_field_formset = _get_system_text_field_formset(system, request.POST)
        if text_field_formset.is_valid():
            for form in text_field_formset:
                system_field = get_object_or_404(SystemFieldText, id=form.cleaned_data["system_field_id"])
                field_instance = SystemFieldTextInstance(relevant_power=power,
                                                         relevant_field=system_field,
                                                         value=form.cleaned_data["field_text"])
                field_instance.save()
        else:
            raise ValueError("Invalid text field formset")
        roll_field_formset = _get_system_roll_field_formset(system, request.POST)
        if roll_field_formset.is_valid():
            for form in roll_field_formset:
                system_field = get_object_or_404(SystemFieldRoll, id=form.cleaned_data["system_field_id"])
                roll = _get_roll_from_form_and_system(form, system_field)
                field_instance = SystemFieldRollInstance(relevant_power=power,
                                                          relevant_field=system_field,
                                                          roll=roll)
                field_instance.save()
        else:
            raise ValueError("Invalid roll field formset")
        return power
    else:
        raise ValueError("Invalid Power Form")

def _get_system_text_field_formset(system, POST = None):
    TextFieldsFormset = formset_factory(SystemFieldTextForm, extra=0)
    text_system_fields = system.systemfieldtext_set.order_by("id").all()
    text_fields_formset = TextFieldsFormset(
        POST,
        initial=[{'system_field_id': x.id, 'system_field': x} for x in text_system_fields],
        prefix="system_text_fields")
    return text_fields_formset


def _get_system_roll_field_formset(system, POST=None):
    RollFieldsFormset = formset_factory(SystemFieldRollForm, extra=0)
    roll_system_fields = system.systemfieldroll_set.order_by("id").all()
    roll_fields_formset = RollFieldsFormset(
        POST,
        initial=[{'system_field_id': x.id, 'system_field': x} for x in roll_system_fields],
        prefix="system_roll_fields")
    return roll_fields_formset

def _get_power_creation_reason(new_power, old_power):
    if old_power is None:
        # new
        return CREATION_REASON[0][0]
    new_points = new_power.get_point_value()
    old_points = old_power.get_point_value()

    if new_points > old_points:
        # improvement
        return CREATION_REASON[1][0]
    if new_points < old_points\
            or _get_param_difference_text(new_power, old_power)\
            or _get_added_enhancements(new_power, old_power)\
            or _get_removed_enhancements(new_power, old_power)\
            or _get_added_drawbacks(new_power, old_power)\
            or _get_removed_drawbacks(new_power, old_power):
        # revision
        return CREATION_REASON[2][0]
    # adjustment
    return CREATION_REASON[3][0]

def _get_power_creation_reason_expanded_text(new_power, old_power):
    edit_text = ""
    if new_power.creation_reason == CREATION_REASON[3][0]:
        edit_text = "Text field change"
    if new_power.creation_reason == CREATION_REASON[1][0] or new_power.creation_reason == CREATION_REASON[2][0]:
        # improvement or revision

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