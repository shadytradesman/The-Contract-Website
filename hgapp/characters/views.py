from random import randint

from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.db import transaction
from django.core import serializers
from collections import defaultdict
from heapq import merge

from characters.models import Character, BasicStats, Character_Death, Graveyard_Header, Attribute, Ability, \
    CharacterTutorial, Asset, Liability, BattleScar
from powers.models import Power_Full
from characters.forms import make_character_form, CharacterDeathForm, ConfirmAssignmentForm, AttributeForm, AbilityForm, \
    AssetForm, LiabilityForm, BattleScarForm
from characters.form_utilities import get_edit_context, character_from_post, update_character_from_post


def create_character(request):
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    if request.method == 'POST':
        with transaction.atomic():
            new_character = character_from_post(request.user, request.POST)
        return HttpResponseRedirect(reverse('characters:characters_view', args=(new_character.id,)))
    else:
        context = get_edit_context(user=request.user)
        return render(request, 'characters/edit_pages/edit_character.html', context)

def edit_character(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_edit(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        with transaction.atomic():
            update_character_from_post(request.user, existing_character=character, POST=request.POST)
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character.id,)))
    else:
        context = get_edit_context(user=request.user, existing_character=character)
        return render(request, 'characters/edit_pages/edit_character.html', context)


def edit_obituary(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    existing_death = character.character_death_set.filter(is_void=False).first()
    if not character.player_can_edit(request.user):
        return HttpResponseForbidden()
    if request.method == 'POST':
        if character.active_game_attendances():
            HttpResponseRedirect(reverse('characters:characters_obituary', args=(character.id,)))
        if existing_death:
            obit_form = CharacterDeathForm(request.POST, instance=existing_death)
            if obit_form.is_valid():
                with transaction.atomic():
                    edited_death = obit_form.save(commit=False)
                    edited_death.is_void = obit_form.cleaned_data['is_void']
                    edited_death.save()
            else:
                print(obit_form.errors)
                return None
        else:
            obit_form=CharacterDeathForm(request.POST)
            if obit_form.is_valid():
                new_character_death = obit_form.save(commit=False)
                new_character_death.relevant_character = character
                new_character_death.date_of_death = timezone.now()
                with transaction.atomic():
                    new_character_death.save()
            else:
                print(obit_form.errors)
                return None
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character.id,)))
    else:
        if existing_death:
            obit_form = CharacterDeathForm(instance=existing_death)
        else:
            obit_form = CharacterDeathForm()
        context = {
            'character': character,
            'obit_form': obit_form,
        }
        return render(request, 'characters/edit_obituary.html', context)


def graveyard(request):
    dead_characters = Character_Death.objects.filter(is_void=False).filter(relevant_character__private=False).order_by('-date_of_death').all()
    num_headers = Graveyard_Header.objects.all().count()
    if num_headers > 0:
        header = Graveyard_Header.objects.all()[randint(0,num_headers-1)].header
    else:
        header = "RIP"
    context = {
        'character_deaths': dead_characters,
        'header': header,
    }
    return render(request, 'characters/graveyard.html', context)


def view_character(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    user_can_edit = request.user.is_authenticated and character.player_can_edit(request.user)
    if not character.player_can_view(request.user):
        return HttpResponseForbidden()
    completed_games = [(x.relevant_game.end_time, "game", x) for x in character.completed_games()]
    character_edit_history = [(x.created_time, "edit", x) for x in
                              character.contractstats_set.filter(is_snapshot=False).order_by("created_time").all()[1:]]
    events_by_date = list(merge(completed_games, character_edit_history))
    timeline = defaultdict(list)
    for event in events_by_date:
        timeline[event[0].strftime("%b %m %Y")].append((event[1], event[2]))

    char_ability_values = character.stats_snapshot.abilityvalue_set.order_by("relevant_ability__name").all()
    char_value_ids = [x.relevant_ability.id for x in char_ability_values]
    primary_zero_values = [(x.name, x, 0) for x in Ability.objects.filter(is_primary=True).order_by("name").all()
                 if x.id not in char_value_ids]
    all_ability_values =[(x.relevant_ability.name, x.relevant_ability, x.value) for x in char_ability_values]
    ability_value_by_name = list(merge(primary_zero_values, all_ability_values))
    context = {
        'character': character,
        'user_can_edit': user_can_edit,
        'health_display': character.get_health_display(),
        'ability_value_by_name': ability_value_by_name,
        'physical_attributes': character.get_attributes(is_physical=True),
        'mental_attributes': character.get_attributes(is_physical=False),
        'timeline': dict(timeline),
        'tutorial': get_object_or_404(CharacterTutorial),
        'battle_scar_form': BattleScarForm(),
    }
    return render(request, 'characters/view_pages/view_character.html', context)


def archive_character(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_view(request.user):
        return HttpResponseForbidden()
    return HttpResponse(character.archive_txt(), content_type='text/plain')


def choose_powers(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if request.user.is_anonymous or not character.player_can_edit(request.user):
        return HttpResponseForbidden()
    assigned_powers = character.power_full_set.all()
    unassigned_powers = request.user.power_full_set.filter(character=None).order_by('-pub_date').all()
    context = {
        'character': character,
        'assigned_powers': assigned_powers,
        'unassigned_powers': unassigned_powers,
    }
    return render(request, 'characters/choose_powers.html', context)


def toggle_power(request, character_id, power_full_id):
    character = get_object_or_404(Character, id=character_id)
    power_full = get_object_or_404(Power_Full, id=power_full_id)
    if not (character.player_can_edit(request.user) and request.user.has_perm('edit_power_full', power_full)):
            return HttpResponseForbidden()
    if request.method == 'POST':
        assignment_form = ConfirmAssignmentForm(request.POST)
        if assignment_form.is_valid():
            if power_full.character == character:
                # Unassign the power
                power_full.character = None
                power_full.save()
                power_full.set_self_and_children_privacy(is_private=False)
                for reward in power_full.reward_list():
                    reward.refund()
            elif not power_full.character:
                # Assign the power
                power_full.character = character
                power_full.save()
                power_full.set_self_and_children_privacy(is_private=character.private)
                rewards_to_be_spent = character.reward_cost_for_power(power_full)
                for reward in rewards_to_be_spent:
                    reward.assign_to_power(power_full.latest_revision())
            return HttpResponseRedirect(reverse('characters:characters_power_picker', args=(character.id,)))
        else:
            print(assignment_form.errors)
            return None
    else:
        rewards_to_be_spent = character.reward_cost_for_power(power_full)
        reward_deficit = power_full.get_point_value() - len(rewards_to_be_spent)
        insufficient_gifts = False
        if len(character.unspent_gifts()) == 0:
            insufficient_gifts = True
        context = {
            'character': character,
            'power_full': power_full,
            'assignment_form': ConfirmAssignmentForm(),
            'insufficient_gifts': insufficient_gifts,
            'reward_deficit': reward_deficit,
            'rewards_to_spend': rewards_to_be_spent,
        }
        return render(request, 'characters/confirm_power_assignment.html', context)

def spend_reward(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_edit(request.user):
        return HttpResponseForbidden()
    context = {
        'character': character,
    }
    return render(request, 'characters/reward_character.html', context)

def post_scar(request, character_id):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        # get the form data
        form = BattleScarForm(request.POST)
        # save the data and after fetch the object in instance
        if form.is_valid() and character.player_can_edit(request.user):
            battle_scar = BattleScar(description = form.cleaned_data['description'],
                                     character=character)
            with transaction.atomic():
                battle_scar.save()
            ser_instance = serializers.serialize('json', [ battle_scar, ])
            # send to client side.
            return JsonResponse({"instance": ser_instance, "id": battle_scar.id}, status=200)
        else:
            # some form errors occured.
            return JsonResponse({"error": form.errors}, status=400)

    # some error occured
    return JsonResponse({"error": ""}, status=400)

def delete_scar(request, scar_id):
    if request.is_ajax and request.method == "POST":
        scar = get_object_or_404(BattleScar, id=scar_id)
        # get the form data
        form = BattleScarForm(request.POST)
        # save the data and after fetch the object in instance
        if scar.character.player_can_edit(request.user):
            with transaction.atomic():
                scar.delete()
            # send to client side.
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": ""}, status=400)