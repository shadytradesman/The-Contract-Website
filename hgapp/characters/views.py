from random import randint

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.core import serializers
from collections import defaultdict
from django.forms import formset_factory
from heapq import merge
from django.http import HttpResponseRedirect

from characters.models import Character, BasicStats, Character_Death, Graveyard_Header, Attribute, Ability, \
    CharacterTutorial, Asset, Liability, BattleScar, Trauma, TraumaRevision, Injury, Source, ExperienceReward
from powers.models import Power_Full
from characters.forms import make_character_form, CharacterDeathForm, ConfirmAssignmentForm, AttributeForm, AbilityForm, \
    AssetForm, LiabilityForm, BattleScarForm, TraumaForm, InjuryForm, SourceValForm, make_allocate_gm_exp_form, EquipmentForm,\
    DeleteCharacterForm
from characters.form_utilities import get_edit_context, character_from_post, update_character_from_post, \
    grant_trauma_to_character, delete_trauma_rev


def __check_edit_perms(request, character, secret_key):
    if hasattr(character, 'player') and character.player:
        requester_can_edit = request.user.is_authenticated and character.player_can_edit(request.user)
    else:
        requester_can_edit = secret_key and character.is_editable_with_key(secret_key)
    if not requester_can_edit:
        raise PermissionDenied("You do not have permission to edit this Character")

def create_character(request):
    if request.user.is_authenticated and not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    if request.method == 'POST':
        with transaction.atomic():
            new_character = character_from_post(request.user, request.POST)
        url_args = (new_character.id,) if request.user.is_authenticated else (new_character.id, new_character.edit_secret_key,)
        return HttpResponseRedirect(reverse('characters:characters_view', args=url_args))
    else:
        context = get_edit_context(user=request.user)
        return render(request, 'characters/edit_pages/edit_character.html', context)

def edit_character(request, character_id, secret_key = None):
    if request.user.is_authenticated and not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    character = get_object_or_404(Character, id=character_id)
    __check_edit_perms(request, character, secret_key)
    if request.method == 'POST':
        with transaction.atomic():
            update_character_from_post(request.user, existing_character=character, POST=request.POST)
        url_args = (character.id,) if request.user.is_authenticated else (character.id, character.edit_secret_key,)
        return HttpResponseRedirect(reverse('characters:characters_view', args=url_args))
    else:
        context = get_edit_context(user=request.user, existing_character=character, secret_key=secret_key)
        return render(request, 'characters/edit_pages/edit_character.html', context)

def delete_character(request, character_id):
    character = get_object_or_404(Character, pk=character_id)
    if not character.player_can_edit(request.user):
        raise PermissionDenied("This Character has been deleted, or you're not allowed to view them")
    if character.player != request.user:
        raise PermissionDenied("Only the creator of a Character can delete them")
    if request.method == 'POST':
        if DeleteCharacterForm(request.POST).is_valid():
            with transaction.atomic():
                character.delete()
        else:
            raise ValueError("could not delete character")
        return HttpResponseRedirect(reverse('home'))
    else:
        context = {"form": DeleteCharacterForm(),
                   "character": character}
        return render(request, 'characters/delete_character.html', context)

def edit_obituary(request, character_id, secret_key = None):
    character = get_object_or_404(Character, id=character_id)
    existing_death = character.character_death_set.filter(is_void=False).first()
    __check_edit_perms(request, character, secret_key)
    if not character.player_can_edit(request.user):
        raise PermissionDenied("You cannot edit this character's obituary")
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
        url_args = (character.id,) if request.user.is_authenticated else (character.id, character.edit_secret_key,)
        return HttpResponseRedirect(reverse('characters:characters_view', args=url_args))
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


def view_character(request, character_id, secret_key = None):
    character = get_object_or_404(Character, id=character_id)
    if character.player and secret_key:
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character_id,)))
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Character")
    if request.user.is_authenticated and not request.user.profile.confirmed_agreements:
            return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    secret_key_valid = False
    if secret_key:
        secret_key_valid = character.is_editable_with_key(secret_key)
    else:
        secret_key = ""
    user_can_edit = (request.user.is_authenticated and character.player_can_edit(request.user)) or secret_key_valid
    if not character.stats_snapshot:
        context={"character": character,
                 "user_can_edit": user_can_edit}
        return render(request, 'characters/legacy_character.html', context)

    completed_games = [(x.relevant_game.end_time, "game", x) for x in character.completed_games()] # completed_games() does ordering
    character_edit_history = [(x.created_time, "edit", x) for x in
                              character.contractstats_set.filter(is_snapshot=False).order_by("created_time").all()[1:]]
    exp_rewards = [(x.created_time, "exp_reward", x) for x in character.experiencereward_set.order_by("created_time").all()]
    events_by_date = list(merge(completed_games, character_edit_history, exp_rewards))
    timeline = defaultdict(list)
    for event in events_by_date:
        timeline[event[0].strftime("%d %b %Y")].append((event[1], event[2]))

    char_ability_values = character.stats_snapshot.abilityvalue_set.order_by("relevant_ability__name").all()
    char_value_ids = [x.relevant_ability.id for x in char_ability_values]
    primary_zero_values = [(x.name, x, 0) for x in Ability.objects.filter(is_primary=True).order_by("name").all()
                 if x.id not in char_value_ids]
    all_ability_values =[(x.relevant_ability.name, x.relevant_ability, x.value) for x in char_ability_values]
    ability_value_by_name = list(merge(primary_zero_values, all_ability_values))
    unspent_experience = character.unspent_experience()
    exp_earned = character.exp_earned()
    exp_cost = character.exp_cost()

    equipment_form = EquipmentForm()
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
        'trauma_form': TraumaForm(prefix="trauma"),
        'injury_form': InjuryForm(request.POST, prefix="injury"),
        'exp_cost': exp_cost,
        'exp_earned': exp_earned,
        'unspent_experience': unspent_experience,
        'equipment_form': equipment_form,
        'secret_key': secret_key,
        'secret_key_valid': secret_key_valid,
    }
    return render(request, 'characters/view_pages/view_character.html', context)


def archive_character(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Character")
    return HttpResponse(character.archive_txt(), content_type='text/plain')


def choose_powers(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if request.user.is_anonymous or not character.player_can_edit(request.user):
        raise PermissionDenied("You do not have permission to edit this Character")
    assigned_powers = character.power_full_set.all()
    unassigned_powers = request.user.power_full_set.filter(character=None, is_deleted=False).order_by('-pub_date').all()
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
        raise PermissionDenied("You do not have permission to edit this Character or the requested Power")
    if request.method == 'POST':
        assignment_form = ConfirmAssignmentForm(request.POST)
        if assignment_form.is_valid():
            with transaction.atomic():
                if power_full.character == character:
                    # Unassign the power
                    power_full.character = None
                    power_full.save()
                    power_full.set_self_and_children_privacy(is_private=False)
                    for reward in power_full.reward_list():
                        reward.refund_keeping_character_assignment()
                elif not power_full.character:
                    if power_full.is_deleted:
                        raise PermissionDenied("This Power has been deleted")
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
        raise PermissionDenied("You do not have permission to edit this Character")
    unassigned_powers = request.user.power_full_set.filter(is_deleted=False, character__isnull=True).all()
    context = {
        'character': character,
        'unassigned_powers': unassigned_powers,
    }
    return render(request, 'characters/reward_character.html', context)

def allocate_gm_exp(request, secret_key = None):
    if not request.user.is_authenticated:
        raise PermissionDenied("You must be logged in to allocate exp")
    users_living_character_ids = [char.id for char in request.user.character_set.filter(is_deleted=False).all() if not char.is_dead()]
    queryset = Character.objects.filter(id__in=users_living_character_ids)
    RewardForm = make_allocate_gm_exp_form(queryset)
    RewardFormset = formset_factory(RewardForm, extra=0)
    if request.method == 'POST':
        reward_formset = RewardFormset(
            request.POST,
            initial=[{"reward": x} for x in request.user.experiencereward_set.filter(rewarded_character=None).all()])
        if reward_formset.is_valid():
            for form in reward_formset:
                reward = get_object_or_404(ExperienceReward, id=form.cleaned_data["reward_id"])
                if reward.rewarded_character or reward.rewarded_player != request.user:
                    raise PermissionDenied("This reward has been allocated, or it isn't yours")
                if "chosen_character" in form.changed_data:
                    char = form.cleaned_data["chosen_character"]
                    if char.player != request.user:
                        raise PermissionDenied("You cannot give your rewards to other people's characters!")
                    reward.rewarded_character = char
                    reward.created_time = timezone.now()
                    with transaction.atomic():
                        reward.save()
            return HttpResponseRedirect(reverse('home'))
        else:
            raise ValueError("Invalid reward forms")
    else:
        reward_formset = RewardFormset(
            initial=[{"reward": x} for x in request.user.experiencereward_set.filter(rewarded_character=None).all()])
        context = {
            'reward_formset': reward_formset,
        }
        return render(request, 'characters/gm_exp_reward.html', context)

def claim_character(request, character_id, secret_key = None):
    if request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        if hasattr(character, 'player') and character.player:
            raise PermissionDenied("This character has already been claimed.")
        __check_edit_perms(request, character, secret_key)
        character.player = request.user
        with transaction.atomic():
            character.save()
            character.set_default_permissions()
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character_id,)))
    return HttpResponseRedirect(reverse('characters:characters_view', args= (character_id, secret_key,)))


#####
# View Character AJAX
####

def post_scar(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        __check_edit_perms(request, character, secret_key)
        form = BattleScarForm(request.POST)
        if form.is_valid():
            battle_scar = BattleScar(description = form.cleaned_data['description'],
                                     character=character)
            with transaction.atomic():
                battle_scar.save()
            ser_instance = serializers.serialize('json', [ battle_scar, ])
            return JsonResponse({"instance": ser_instance, "id": battle_scar.id}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)

    return JsonResponse({"error": ""}, status=400)

def delete_scar(request, scar_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        scar = get_object_or_404(BattleScar, id=scar_id)
        character = scar.character
        __check_edit_perms(request, character, secret_key)
        with transaction.atomic():
            scar.delete()
        return JsonResponse({}, status=200)
    return JsonResponse({"error": ""}, status=400)

def post_trauma(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        form = TraumaForm(request.POST, prefix="trauma")
        __check_edit_perms(request, character, secret_key)
        if form.is_valid():
            with transaction.atomic():
                trauma_rev = grant_trauma_to_character(form, character)
            return JsonResponse({"id": trauma_rev.id, "description": trauma_rev.relevant_trauma.description}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": ""}, status=400)

def delete_trauma(request, trauma_rev_id, used_xp, secret_key = None):
    if request.is_ajax and request.method == "POST":
        trauma_rev = get_object_or_404(TraumaRevision, id=trauma_rev_id)
        character = trauma_rev.relevant_stats.assigned_character
        __check_edit_perms(request, character, secret_key)
        with transaction.atomic():
            delete_trauma_rev(character, trauma_rev, True if used_xp == "T" else False)
        return JsonResponse({}, status=200)
    return JsonResponse({"error": ""}, status=400)

def post_injury(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        form = InjuryForm(request.POST, prefix="injury")
        __check_edit_perms(request, character, secret_key)
        if form.is_valid():
            injury = Injury(description = form.cleaned_data['description'],
                            character=character,
                            severity = form.cleaned_data['severity'])
            with transaction.atomic():
                injury.save()
            ser_instance = serializers.serialize('json', [ injury, ])
            return JsonResponse({"instance": ser_instance, "id": injury.id, "severity": injury.severity}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": ""}, status=400)

def delete_injury(request, injury_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        injury = get_object_or_404(Injury, id=injury_id)
        form = InjuryForm(request.POST, prefix="injury")
        __check_edit_perms(request, injury.character, secret_key)
        with transaction.atomic():
            injury.delete()
        return JsonResponse({}, status=200)
    return JsonResponse({"error": ""}, status=400)

def set_mind_damage(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        form = InjuryForm(request.POST, prefix="mental-exertion")
        __check_edit_perms(request, character, secret_key)
        if form.is_valid():
            requested_damage = form.cleaned_data['severity']
            num_mind = character.num_mind_levels()
            if requested_damage > num_mind:
                character.mental_damage = num_mind
            elif requested_damage < 0:
                character.mental_damage = 0
            else:
                character.mental_damage = requested_damage
            with transaction.atomic():
                character.save()
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": ""}, status=400)


def set_source_val(request, source_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        source = get_object_or_404(Source, id=source_id)
        form = SourceValForm(request.POST, prefix="source")
        __check_edit_perms(request, source.owner, secret_key)
        if form.is_valid():
            source.current_val = form.cleaned_data['value']
            with transaction.atomic():
                source.save()
            return JsonResponse({}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": ""}, status=400)

def post_equipment(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        form = EquipmentForm(request.POST)
        __check_edit_perms(request, character, secret_key)
        if form.is_valid():
            character.equipment=form.cleaned_data['equipment']
            with transaction.atomic():
                character.save()
            return JsonResponse({"equipment": form.cleaned_data['equipment']}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)

    return JsonResponse({"error": ""}, status=400)