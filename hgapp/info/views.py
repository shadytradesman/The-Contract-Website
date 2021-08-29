from django.shortcuts import render
from .terms import EULA, TERMS, PRIVACY
from django.shortcuts import get_object_or_404
from info.models import FrontPageInfo, QuickStartInfo, ExampleAction
from characters.models import CharacterTutorial

def getting_started(request):
    return render(request, 'info/getting_started.html')

def terms(request):
    context= {
        "terms": TERMS,
        "eula": EULA,
        "privacy": PRIVACY,
    }
    return render(request, 'info/terms.html', context)

def probability(request):
    return render(request, 'info/probability.html')

def fiction(request):
    info = FrontPageInfo.objects.first()
    context= {
        "info": info,
    }
    return render(request, 'info/fiction.html', context)

def quickstart(request):
    quickstart_info = QuickStartInfo.objects.first()
    character = quickstart_info.main_char
    attribute_val_by_id = character.get_attribute_values_by_id()
    ability_val_by_id = character.get_ability_values_by_id()
    actions = ExampleAction.objects.filter(is_first_roll=False).all()
    first_action = ExampleAction.objects.filter(is_first_roll=True).get()
    character_tutorial = get_object_or_404(CharacterTutorial)
    action_list = []
    physical_attributes = character.get_attributes(is_physical=True)
    mental_attributes = character.get_attributes(is_physical=False)
    for action in actions:
        action_list.append(action.json_serialize())
    abilities = character.stats_snapshot.abilityvalue_set.all()
    context= {
        "quickstart_info": quickstart_info,
        "character": character,
        "physical_attributes": physical_attributes,
        "mental_attributes": mental_attributes,
        "abilities": abilities,
        "attribute_value_by_id": attribute_val_by_id,
        "ability_value_by_id": ability_val_by_id,
        "action_list": action_list,
        "first_action": first_action.json_serialize(),
        "tutorial": character_tutorial,
    }
    return render(request, 'info/new_player_guide/quickstart.html', context)
