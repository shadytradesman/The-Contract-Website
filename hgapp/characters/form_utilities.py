from django.forms import formset_factory

from characters.models import Character, BasicStats, Character_Death, Graveyard_Header, Attribute, Ability, \
    CharacterTutorial, Asset, Liability, AttributeValue, ContractStats, AbilityValue, LiabilityDetails, AssetDetails
from powers.models import Power_Full
from characters.forms import make_character_form, CharacterDeathForm, ConfirmAssignmentForm, AttributeForm, AbilityForm, \
    AssetForm, LiabilityForm
from collections import defaultdict
from django.utils import timezone
from django.shortcuts import get_object_or_404

# logic for Character creation and editing
# TRANSACTIONS HAPPEN IN VIEW LAYER
# See tests.py for hints on how revisioning works.

def __get_attribute_formset_for_edit(existing_character, AttributeFormSet, POST=None):
    return AttributeFormSet(
        POST,
        initial=[{'attribute_id': x.relevant_attribute.id,
                  'value': x.value,
                  'attribute': x.relevant_attribute,
                  'previous_value_id': x.previous_revision.id if x.previous_revision else None}
                 for x in existing_character.stats_snapshot.attributevalue_set.order_by('relevant_attribute__name').all()],
        prefix="attributes")

def get_edit_context(user, existing_character=None):
    char_form = make_character_form(user)(instance=existing_character)
    AttributeFormSet = formset_factory(AttributeForm, extra=0)
    AbilityFormSet = formset_factory(AbilityForm, extra=1)
    attributes = Attribute.objects.order_by('name')
    tutorial = get_object_or_404(CharacterTutorial)
    if existing_character and existing_character.stats_snapshot:
        asset_formsets = __get_asset_formsets(existing_character)
        liability_formsets = __get_liability_formsets(existing_character)
        ability_formset = __get_ability_formset_for_edit(existing_character, AbilityFormSet)
        attribute_formset = __get_attribute_formset_for_edit(existing_character, AttributeFormSet)
    else:
        asset_formsets = __get_asset_formsets()
        liability_formsets = __get_liability_formsets()
        attribute_formset = AttributeFormSet(
            initial=[{'attribute_id': x.id, 'value': 1, 'attribute': x} for x in attributes],
            prefix="attributes")
        default_abilities = Ability.objects.filter(is_primary=True).order_by('name')
        ability_formset = AbilityFormSet(
            initial=[{'ability_id': x.id, 'value': 0, 'ability': x} for x in default_abilities],
            prefix="abilities")
    context = {
        'char_form': char_form,
        'attribute_formset': attribute_formset,
        'ability_formset': ability_formset,
        'asset_formsets': asset_formsets,
        'liability_formsets': liability_formsets,
        'tutorial': tutorial,
        'character': existing_character,
    }
    return context

def character_from_post(user, POST):
    char_form = make_character_form(user)(POST)
    if char_form.is_valid():
        new_character = char_form.save(commit=False)
        new_character.pub_date = timezone.now()
        new_character.edit_date = timezone.now()
        new_character.player = user
        new_character.save()
        __save_stats_diff_from_post(POST, new_character=new_character)
        new_character.regen_stats_snapshot()
        cell = char_form.cleaned_data['cell']
        if cell != "free":
            new_character.cell = cell
        new_character.save()
        return new_character
    else:
        raise ValueError("Invalid char_form")

def update_character_from_post(user, POST, existing_character):
    char_form = make_character_form(user)(POST, instance=existing_character)
    if char_form.is_valid():
        char_form.save(commit=False)
        existing_character.edit_date = timezone.now()
        existing_character.cell = char_form.cleaned_data['cell']
        existing_character.save()
        if existing_character.private != char_form.cleaned_data['private']:
            for power_full in existing_character.power_full_set.all():
                power_full.set_self_and_children_privacy(is_private=char_form.cleaned_data['private'])
        if existing_character.stats_snapshot:
            __save_stats_diff_from_post(POST=POST, existing_character=existing_character)
        else:
            __save_stats_diff_from_post(POST=POST, new_character=existing_character)
        existing_character.regen_stats_snapshot()
    else:
        raise ValueError("invalid edit char_form")

# __private methods

def __save_stats_diff_from_post(POST, existing_character=None, new_character=None):
    if new_character:
        # Create the character's stats snapshot and save.
        stats_snapshot = ContractStats(assigned_character=new_character,
                                       is_snapshot=True)
        stats_snapshot.save()
        new_character.stats_snapshot = stats_snapshot
        new_character.save()
    AttributeFormSet = formset_factory(AttributeForm, extra=0)
    AbilityFormSet = formset_factory(AbilityForm, extra=1)
    attributes = Attribute.objects.order_by('name')
    asset_formsets = __get_asset_formsets(existing_character, POST=POST)
    liability_formsets = __get_liability_formsets(existing_character, POST=POST)
    if existing_character:
        stats = ContractStats(assigned_character=existing_character)
        stats.save()
        for asset_formset in asset_formsets:
            __save_edit_quirks_from_formset(formset=asset_formset, stats=stats, is_asset=True)
        for liability_formset in liability_formsets:
            __save_edit_quirks_from_formset(formset=liability_formset, stats=stats, is_asset=False)
        ability_formset = __get_ability_formset_for_edit(existing_character, AbilityFormSet, POST)
        __save_edit_abilities_from_formset(formset=ability_formset, stats=stats)
        attribute_formset = __get_attribute_formset_for_edit(existing_character, AttributeFormSet, POST)
        attribute_formset.is_valid
        for form in attribute_formset:
            if form.is_valid():
                attribute = get_object_or_404(Attribute, id=form.cleaned_data['attribute_id'])
                if "previous_value_id" in form.cleaned_data and form.cleaned_data["previous_value_id"]:
                    value_id = form.cleaned_data['previous_value_id']
                    prev_val = get_object_or_404(AttributeValue, id=value_id)
                    if form.changed_data and form.cleaned_data['value'] != str(prev_val.value):
                        new_val = AttributeValue(
                            relevant_stats=stats,
                            relevant_attribute=attribute,
                            value=form.cleaned_data['value'],
                            previous_revision=prev_val,
                        )
                        new_val.save()
                else:
                    raise ValueError("The site doesn't support adding attribute until you implement this.")
            else:
                raise ValueError("invalid attribute form in edit")


    else: # new character
        stats = ContractStats(assigned_character=new_character)
        stats.save()
        attribute_formset = AttributeFormSet(POST,
                                             initial=[{'attribute_id': x.id, 'value': 1, 'attribute': x} for x in attributes],
                                             prefix="attributes")
        default_abilities = Ability.objects.filter(is_primary=True).order_by('name')
        ability_formset = AbilityFormSet(POST,
                                         initial=[{'ability_id': x.id, 'value': 0, 'ability': x} for x in
                                                  default_abilities],
                                         prefix="abilities")
        attribute_values = __attributes_from_form(attribute_formset, stats)
        ability_values = __abilities_from_form(ability_formset, stats)
        liabilities = __liabilities_from_formsets(liability_formsets, stats)
        assets = __assets_from_formsets(asset_formsets, stats)
    stats.save()
    return stats

def __liabilities_from_formsets(liability_formsets, stats):
    liability_details = []
    for liability_formset in liability_formsets:
        if liability_formset.is_valid():
            liability = get_object_or_404(Liability, id=liability_formset.initial[0]["id"])
            for form in liability_formset:
                if form.cleaned_data['is_selected']:
                    deets = LiabilityDetails(
                        relevant_stats=stats,
                        relevant_liability=liability,
                        details=form.cleaned_data['details'] if 'details' in form.cleaned_data else "",
                    )
                    deets.save()
                    liability_details.append(deets)
        else:
            raise ValueError("Invalid liability formset")
    return liability_details

def __assets_from_formsets(asset_formsets, stats):
    asset_details = []
    for asset_formset in asset_formsets:
        if asset_formset.is_valid():
            asset = get_object_or_404(Asset, id=asset_formset.initial[0]["id"])
            for form in asset_formset:
                if form.cleaned_data['is_selected']:
                    new_asset_deets = AssetDetails(
                        relevant_stats=stats,
                        relevant_asset=asset,
                        details= form.cleaned_data['details'] if 'details' in form.cleaned_data else "",
                    )
                    new_asset_deets.save()
                    asset_details.append(new_asset_deets)
        else:
            raise ValueError("Invalid liability formset")
    return asset_details

def __attributes_from_form(attribute_formset, stats):
    if attribute_formset.is_valid():
        attribute_values = []
        for form in attribute_formset:
            attr_value = AttributeValue(
                relevant_attribute=get_object_or_404(Attribute, id=form.cleaned_data['attribute_id']),
                value=form.cleaned_data['value'],
                relevant_stats=stats,
            )
            attr_value.save()
            attribute_values.append(attr_value)
        return attribute_values
    else:
        raise ValueError("Invalid Attribute Formset")

def __abilities_from_form(ability_formset, stats):
    if ability_formset.is_valid():
        ability_values = []
        for form in ability_formset:
            __new_ability_from_form(form, stats)

        return ability_values
    else:
        raise ValueError("Invalid Ability Formset")

def __new_ability_from_form(form, stats):
    ability = None
    if 'ability_id' in form.cleaned_data and form.cleaned_data['ability_id']:
        ability = get_object_or_404(Ability, id=form.cleaned_data['ability_id'])
    elif 'name' in form.cleaned_data:
        ability = Ability(
            name=form.cleaned_data['name'],
            tutorial_text=form.cleaned_data['description'] if 'description' in form.cleaned_data else "",
        )
        ability.save()
    if 'value' in form.cleaned_data and form.cleaned_data['value'] > 0:
        ability_value = AbilityValue(
            relevant_ability=ability,
            value=form.cleaned_data['value'],
            relevant_stats=stats,
        )
        ability_value.save()
        return ability_value

def __get_asset_formsets(existing_character = None, POST = None):
    asset_formsets = []
    AssetFormSet = formset_factory(AssetForm, extra=0)
    if existing_character:
        asset_details = existing_character.stats_snapshot.assetdetails_set.order_by('relevant_asset__value', 'id').all()
        details_by_asset_id = defaultdict(list)
        for details in asset_details:
            details_by_asset_id[details.relevant_asset.id].append(details)
        asset_formsets = __get_quirk_formsets_for_edit_context(POST=POST,
                                                               details_by_quirk_id=details_by_asset_id,
                                                               is_asset=True,
                                                               all_quirks=Asset.objects.order_by('value').all())
    else:
        for asset in Asset.objects.order_by('value').all():
            asset_formsets.append(AssetFormSet(POST,
                                               initial=[{'id': asset.id, 'quirk': asset}],
                                               prefix="asset-" + str(asset.id)))
    return asset_formsets

def __get_liability_formsets(existing_character = None, POST = None):
    liability_formsets = []
    LiabilityFormSet = formset_factory(LiabilityForm, extra=0)
    if existing_character:
        liability_details = existing_character.stats_snapshot.liabilitydetails_set.order_by('relevant_liability__value', 'id').all()
        details_by_liability_id = defaultdict(list)
        for details in liability_details:
            details_by_liability_id[details.relevant_liability.id].append(details)
        liability_formsets = __get_quirk_formsets_for_edit_context(POST=POST,
                                                                   details_by_quirk_id=details_by_liability_id,
                                                                   is_asset=False,
                                                                   all_quirks=Liability.objects.order_by('value').all())
    else:
        for liability in Liability.objects.order_by('value').all():
            liability_formsets.append(LiabilityFormSet(POST,
                                                       initial=[{'id': liability.id, 'quirk': liability}],
                                                       prefix="liability-" + str(liability.id)))
    return liability_formsets


def __get_quirk_formsets_for_edit_context(details_by_quirk_id, is_asset, all_quirks, POST = None):
    FormSet = formset_factory(AssetForm, extra=0) if is_asset else formset_factory(LiabilityForm, extra=0)
    prefix = "asset" if is_asset else "liability"
    quirk_formsets = []
    for quirk in all_quirks:
        if quirk.id in details_by_quirk_id:
            initial_data = [{'id': quirk.id,
                             'quirk': quirk,
                             'details': detail.details,
                             # the stat snapshot details point to stat diff details using the previous_revision field
                             # It is important to point to the diff details because snapshot details may be deleted.
                             'details_id': detail.previous_revision.id,
                             'is_selected': True,
                             } for detail in details_by_quirk_id[quirk.id]]
            # additional empty form if multiplicity is allowed.
            if quirk.multiplicity_allowed and len(details_by_quirk_id[quirk.id]) < 4:
                initial_data.append({'id': quirk.id,
                                     'quirk': quirk,})
            quirk_formsets.append(FormSet(POST,
                                          initial=initial_data,
                                          prefix=prefix + str(quirk.id)))
        else:
            quirk_formsets.append(FormSet(POST,
                                          initial=[{'id': quirk.id, 'quirk': quirk}],
                                          prefix=prefix + str(quirk.id)))
    return quirk_formsets

def __save_edit_quirks_from_formset(formset, stats, is_asset):
    Quirk = Asset if is_asset else Liability
    QuirkDetails = AssetDetails if is_asset else LiabilityDetails
    if formset.is_valid():
        quirk = get_object_or_404(Quirk, id=formset.initial[0]["id"])
        for form in formset:
            if form.cleaned_data["details_id"]:
                details_id = form.cleaned_data['details_id']
                prev_details = get_object_or_404(QuirkDetails, id=details_id)
                if form.changed_data:
                    new_details = QuirkDetails(
                        relevant_stats=stats,
                        # we only show selected quirks, so if the selection status has changed, they unselected it
                        is_deleted='is_selected' in form.changed_data,
                        details=form.cleaned_data['details'],
                        previous_revision=prev_details,
                    )
                    if is_asset:
                        new_details.relevant_asset=quirk
                    else:
                        new_details.relevant_liability=quirk
                    new_details.save()
            else:
                # No pre-existing details_id means this is a new quirk.
                if form.cleaned_data['is_selected']:
                    new_quirk_deets = QuirkDetails(
                        relevant_stats=stats,
                        details=form.cleaned_data['details'] if 'details' in form.cleaned_data else "",
                    )
                    if is_asset:
                        new_quirk_deets.relevant_asset = quirk
                    else:
                        new_quirk_deets.relevant_liability = quirk
                    new_quirk_deets.save()
    else:
        raise ValueError("invalid quirk formset from edit post")

def __get_ability_formset_for_edit(existing_character, AbilityFormSet, POST = None):
    default_abilities = Ability.objects.filter(is_primary=True).order_by('name')
    ability_values = existing_character.stats_snapshot.abilityvalue_set.all()
    values_by_ability_id = {x.relevant_ability.id: x for x in ability_values}
    initial_abilities = [{'ability_id': x.id,
                          'value': values_by_ability_id[x.id].value if x.id in values_by_ability_id else 0,
                          'ability': x,
                          'value_id': values_by_ability_id[x.id].previous_revision.id if x.id in values_by_ability_id else None}
                         for x in default_abilities]
    for value in ability_values:
        if value.relevant_ability not in default_abilities:
            initial_abilities.append({
                'ability_id': value.relevant_ability.id,
                'value': value.value,
                'ability': value.relevant_ability,
                'value_id': value.previous_revision.id})
    ability_formset = AbilityFormSet(POST,
        initial=initial_abilities,
        prefix="abilities")
    return ability_formset

def __save_edit_abilities_from_formset(formset, stats):
    for form in formset:
        if form.is_valid():
            if 'ability_id' in form.cleaned_data and form.cleaned_data['ability_id']:
                ability = get_object_or_404(Ability, id=form.cleaned_data['ability_id'])
            elif 'name' in form.cleaned_data:
                ability = Ability(
                    name=form.cleaned_data['name'],
                    tutorial_text=form.cleaned_data['description'] if 'description' in form.cleaned_data else "",
                )
                ability.save()
            if "value_id" in form.cleaned_data and form.cleaned_data["value_id"]:
                value_id = form.cleaned_data['value_id']
                prev_val = get_object_or_404(AbilityValue, id=value_id)
                if form.changed_data:
                    # ability.id == pre_val check makes it harder to edit arbitrary abilities
                    # TODO: add ownership to secondary abilities somehow
                    if "description" in form.changed_data and ability and ability.id == prev_val.relevant_ability.id and not ability.is_primary:
                        ability.description = form.cleaned_data['description']
                        ability.save()
                    if prev_val.value != form.cleaned_data['value']:
                        # if it's changed, we write the whole thing.
                        new_val = AbilityValue(
                            relevant_stats=stats,
                            relevant_ability=ability,
                            value=form.cleaned_data['value'],
                            previous_revision=prev_val,
                        )
                        new_val.save()
            else:
                # No pre-existing value_id means this is a new ability.
                __new_ability_from_form(form, stats)
        else:
            raise ValueError("invalid ability form in edit")
