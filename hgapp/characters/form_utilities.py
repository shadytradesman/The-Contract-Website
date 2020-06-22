from django.forms import formset_factory

from characters.models import Character, BasicStats, Character_Death, Graveyard_Header, Attribute, Ability, \
    CharacterTutorial, Asset, Liability, AttributeValue, ContractStats, AbilityValue
from powers.models import Power_Full
from characters.forms import make_character_form, CharacterDeathForm, ConfirmAssignmentForm, AttributeForm, AbilityForm, \
    AssetForm, LiabilityForm
from django.shortcuts import get_object_or_404

def get_edit_context(user, existing_character=None):
    char_form = make_character_form(user)()
    AttributeFormSet = formset_factory(AttributeForm, extra=0)
    AbilityFormSet = formset_factory(AbilityForm, extra=1)
    AssetFormSet = formset_factory(AssetForm, extra=0)# 1 if edit?? idk
    LiabilityFormSet = formset_factory(LiabilityForm, extra=0)
    attributes = Attribute.objects.order_by('name')
    tutorial = get_object_or_404(CharacterTutorial)
    attribute_formset = None
    ability_formset = None
    asset_formsets = None
    liability_formsets = None
    if existing_character:
        pass
    else:
        attribute_formset = AttributeFormSet(
            initial=[{'attribute_id': x.id, 'value': 1, 'attribute': x} for x in attributes],
            prefix="attributes")
        default_abilities = Ability.objects.filter(is_primary=True).order_by('name')
        ability_formset = AbilityFormSet(
            initial=[{'ability_id': x.id, 'value': 0, 'ability': x} for x in default_abilities],
            prefix="abilities")
        asset_formsets = []
        for asset in Asset.objects.order_by('value').all():
            asset_formsets.append(AssetFormSet(initial=[{'id': asset.id, 'quirk': asset}],
                                               prefix="asset-" + str(asset.id)))
        liability_formsets = []
        for liability in Liability.objects.order_by('value').all():
            liability_formsets.append(LiabilityFormSet(initial=[{'id': liability.id, 'quirk': liability}],
                                                       prefix="liability-" + str(liability.id)))
    context = {
        'char_form': char_form,
        'attribute_formset': attribute_formset,
        'ability_formset': ability_formset,
        'asset_formsets': asset_formsets,
        'liability_formsets': liability_formsets,
        'tutorial': tutorial,
    }
    return context

# TRANSACTIONS HAPPEN IN VIEW LAYER
def character_from_post(user, POST, existing_character=None):
    # put forms together
    char_form = make_character_form(user)(POST)

    AttributeFormSet = formset_factory(AttributeForm, extra=0)
    AbilityFormSet = formset_factory(AbilityForm, extra=1)
    AssetFormSet = formset_factory(AssetForm, extra=0)  # 1 if edit?? idk
    LiabilityFormSet = formset_factory(LiabilityForm, extra=0)
    attributes = Attribute.objects.order_by('name')
    # Same initial values as before must be passed in, so this is where we split.
    if existing_character:
        pass # edit
    else: # new character
        attribute_formset = AttributeFormSet(POST,
                                             initial=[{'attribute_id': x.id, 'value': 1, 'attribute': x} for x in attributes],
                                             prefix="attributes")
        default_abilities = Ability.objects.filter(is_primary=True).order_by('name')
        ability_formset = AbilityFormSet(POST,
                                         initial=[{'ability_id': x.id, 'value': 0, 'ability': x} for x in
                                                  default_abilities],
                                         prefix="abilities")

        asset_formsets = []
        for asset in Asset.objects.order_by('value').all():
            asset_formsets.append(AssetFormSet(POST,
                                               initial=[{'id': asset.id, 'quirk': asset}],
                                               prefix="asset-" + str(asset.id)))
        liability_formsets = []
        for liability in Liability.objects.order_by('value').all():
            liability_formsets.append(LiabilityFormSet(POST,
                                                     initial=[{'id': liability.id, 'quirk': liability}],
                                                     prefix="liability-" + str(liability.id)))
        stats = ContractStats()
        attribute_values = __attributes_from_form(attribute_formset, stats)
        ability_values = __abilities_from_form(ability_formset, stats)
        if ability_formset.is_valid():
            pass

        liabilities = []
        for liability_formset in liability_formsets:
            if liability_formset.isValid():
                for form in liability_formset:
                    liabilities.append(Liability(
                        name=form.cleaned_data['name']
                    ))

# rest of the methods are __private
def __attributes_from_form(attribute_formset, stats):
    if attribute_formset.is_valid():
        attribute_values = []
        for form in attribute_formset:
            attribute_values.append(AttributeValue(
                relevant_attribute=get_object_or_404(Attribute, id=form.cleaned_data['attribute_id']),
                value=form.cleaned_data['value'],
                relevant_stats=stats,
            ))
        return attribute_values
    else:
        raise ValueError("Invalid Attribute Formset")

def __abilities_from_form(ability_formset, stats):
    if ability_formset.is_valid():
        ability_values = []
        for form in ability_formset:
            ability = None
            if 'ability_id' in form.cleaned_data and form.cleaned_data['ability_id']:
                ability = get_object_or_404(Ability, id=form.cleaned_data['ability_id'])
            elif 'name' in form.cleaned_data:
                ability = Ability(
                    name=form.cleaned_data['name'],
                    tutorial_text= form.cleaned_data['description'] if 'description' in form.cleaned_data else "",
                )
            if 'value' not in form.cleaned_data:
                pass
            else:
                ability_values.append(AbilityValue(
                    relevant_ability=ability,
                    value=form.cleaned_data['value'],
                    relevant_stats=stats,
                ))
        return ability_values
    else:
        raise ValueError("Invalid Ability Formset")