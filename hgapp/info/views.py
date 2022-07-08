from django.shortcuts import render
from .terms import EULA, TERMS, PRIVACY
from django.shortcuts import get_object_or_404
from heapq import merge
from django.templatetags.static import static
from info.models import FrontPageInfo, QuickStartInfo, ExampleAction
from profiles.models import Profile
from characters.models import CharacterTutorial, Ability, Character
from characters.forms import InjuryForm
from powers.models import Base_Power
from info.models import FrontPageInfo
from profiles.models import Profile
from characters.models import CharacterTutorial, Ability, Character
from games.models import Scenario

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

def leaderboard(request):
    num_to_fetch = 10
    top_gms = Profile.objects.order_by('-num_games_gmed')[:num_to_fetch]
    deadliest_gms = Profile.objects.order_by('-num_gm_kills')[:num_to_fetch]
    most_social_gms = Profile.objects.order_by('-num_gmed_players')[:num_to_fetch]

    top_players = Profile.objects.order_by('-num_player_games')[:num_to_fetch]
    top_ringer_players = Profile.objects.order_by('-num_played_ringers')[:num_to_fetch]
    top_survivors = Profile.objects.order_by('-num_player_survivals')[:num_to_fetch]

    top_contractor_wins = Character.objects.order_by('-num_victories')[:num_to_fetch]
    top_contractor_losses = Character.objects.order_by('-num_losses')[:num_to_fetch]
    top_contractor_journals = Character.objects.order_by('-num_journals')[:num_to_fetch]

    top_scenario_runs = Scenario.objects.order_by('-times_run', '-num_gms_run')[:num_to_fetch]
    top_scenario_gms = Scenario.objects.order_by('-num_gms_run', '-times_run')[:num_to_fetch]
    top_scenario_deadliness = Scenario.objects.filter(num_gms_run__gt=2).order_by('-deadliness_ratio')[:num_to_fetch]

    context = {
        "top_players": top_players,
        "top_ringer_players": top_ringer_players,
        "top_survivors": top_survivors,

        "top_gms": top_gms,
        "deadliest_gms": deadliest_gms,
        "most_social_gms": most_social_gms,

        "top_contractor_wins": top_contractor_wins,
        "top_contractor_losses": top_contractor_losses,
        "top_contractor_journals": top_contractor_journals,

        "top_scenario_runs": top_scenario_runs,
        "top_scenario_gms": top_scenario_gms,
        "top_scenario_deadliness": top_scenario_deadliness,
    }
    return render(request, 'info/leaderboard/leaderboard.html', context)


def how_to_play(request):
    quickstart_info = QuickStartInfo.objects.first()
    character = quickstart_info.main_char
    attribute_val_by_id = character.get_attribute_values_by_id()
    actions = ExampleAction.objects.filter(is_first_roll=False).all()
    first_action = ExampleAction.objects.filter(is_first_roll=True).get()
    character_tutorial = get_object_or_404(CharacterTutorial)
    action_list = []
    physical_attributes = character.get_attributes(is_physical=True)
    mental_attributes = character.get_attributes(is_physical=False)
    char_ability_values = character.stats_snapshot.abilityvalue_set.order_by("relevant_ability__name").all()
    ability_value_by_id = {}
    char_value_ids = [x.relevant_ability.id for x in char_ability_values]
    primary_zero_values = [(x.name, x, 0) for x in Ability.objects.filter(is_primary=True).order_by("name").all()
                           if x.id not in char_value_ids]
    all_ability_values = []
    for x in char_ability_values:
        all_ability_values.append((x.relevant_ability.name, x.relevant_ability, x.value))
        ability_value_by_id[x.relevant_ability.id] = x.value
    ability_value_by_name = list(merge(primary_zero_values, all_ability_values))
    for action in actions:
        action_list.append(action.json_serialize())

    expand_step = []
    expand_step.append(True) # zero index fix
    expand_step.append(not request.user.is_authenticated) #login
    expand_step.append(not request.user.is_authenticated or request.user.character_set.count() == 0) # create contractor
    expand_step.append(not request.user.is_authenticated or request.user.cell_set.count() == 0) # create / join Playgroup
    context= {
        "quickstart_info": quickstart_info,
        "character": character,
        'health_display': character.get_health_display(),
        'injury_form': InjuryForm(request.POST, prefix="injury"),
        "physical_attributes": physical_attributes,
        "mental_attributes": mental_attributes,
        "attribute_value_by_id": attribute_val_by_id,
        "ability_value_by_id": ability_value_by_id,
        "ability_value_by_name": ability_value_by_name,
        "action_list": action_list,
        "first_action": first_action.json_serialize(),
        "tutorial": character_tutorial,
        "expand_step": expand_step,
        'powers_modal_art_url': static('overrides/art/grace.png'),
        'sig_item_modal_art_url': static('overrides/art/lady_lake_sm.jpg'),
        'art_craft_modal_art_url': static('overrides/art/front-music.jpg'),
        'consumable_craft_modal_art_url': static('overrides/art/sushi.jpg'),
        'mod_power': get_object_or_404(Base_Power, slug='power'),
        'mod_sig_item': get_object_or_404(Base_Power, slug='signature-item-mod'),
        'mod_consumable': get_object_or_404(Base_Power, slug='craftable-consumable'),
        'mod_artifacts': get_object_or_404(Base_Power, slug='craftable-artifact'),
    }
    return render(request, 'info/new_player_guide/quickstart.html', context)
