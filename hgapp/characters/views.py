from random import randint

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.core import serializers
from collections import defaultdict
from heapq import merge
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.middleware.csrf import rotate_token


from characters.models import Character, BasicStats, Character_Death, Graveyard_Header, Attribute, Ability, \
    CharacterTutorial, Asset, Liability, BattleScar, Trauma, TraumaRevision, Injury, Source, ExperienceReward, Artifact, \
    LOST, DESTROYED
from powers.models import Power_Full, SYS_LEGACY_POWERS, SYS_PS2, CRAFTING_NONE, CRAFTING_SIGNATURE, CRAFTING_ARTIFACT, \
    CRAFTING_CONSUMABLE
from characters.forms import make_character_form, CharacterDeathForm, ConfirmAssignmentForm, AttributeForm, get_ability_form, \
    AssetForm, LiabilityForm, BattleScarForm, TraumaForm, InjuryForm, SourceValForm, make_allocate_gm_exp_form, EquipmentForm,\
    DeleteCharacterForm, BioForm, make_world_element_form, get_default_scar_choice_field, make_artifact_status_form, \
    make_transfer_artifact_form
from characters.form_utilities import get_edit_context, character_from_post, update_character_from_post, \
    grant_trauma_to_character, delete_trauma_rev, get_world_element_class_from_url_string
from characters.view_utilities import get_characters_next_journal_credit, get_world_element_default_dict, get_weapons_by_type

from journals.models import Journal, JournalCover
from cells.models import Cell

from hgapp.utilities import get_object_or_none

from games.game_utilities import get_character_contacts

def __check_edit_perms(request, character, secret_key=None):
    requester_can_edit = False
    if request.user.is_superuser:
        return True
    if hasattr(character, 'player') and character.player:
        requester_can_edit = request.user.is_authenticated and character.player_can_edit(request.user)
    elif secret_key:
        requester_can_edit = secret_key and character.is_editable_with_key(secret_key)
    if not requester_can_edit:
        raise PermissionDenied("You do not have permission to edit this Character")


def create_character(request, cell_id=None):
    if request.user.is_authenticated and not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    cell = get_object_or_404(Cell, id=cell_id) if cell_id else None
    if request.method == 'POST':
        with transaction.atomic():
            new_character = character_from_post(request.user, request.POST, cell)
        url_args = (new_character.id,) if request.user.is_authenticated else (new_character.id, new_character.edit_secret_key,)
        return HttpResponseRedirect(reverse('characters:characters_view', args=url_args))
    else:
        context = get_edit_context(user=request.user, cell=cell)
        return render(request, 'characters/edit_pages/edit_character.html', context)


def edit_character(request, character_id, secret_key = None):
    if request.user.is_authenticated and not request.user.profile.confirmed_agreements:
        return HttpResponseRedirect(reverse('profiles:profiles_terms'))
    character = get_object_or_404(Character, id=character_id)
    __check_edit_perms(request, character, secret_key)
    if request.method == 'POST':
        with transaction.atomic():
            character = Character.objects.select_for_update(nowait=True).get(pk=character.pk)
            update_character_from_post(request.user, existing_character=character, POST=request.POST)
        url_args = (character.id,) if request.user.is_authenticated else (character.id, character.edit_secret_key,)
        return HttpResponseRedirect(reverse('characters:characters_view', args=url_args))
    else:
        rotate_token(request)  # Prevent interleaved edit form submissions.
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
                character.delete_char()
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
    dead_characters = Character_Death.objects.filter(is_void=False)\
        .filter(relevant_character__private=False)\
        .exclude(relevant_character__status='ANY') \
        .exclude(relevant_character__num_games=0) \
        .order_by('-date_of_death')\
        .all()
    tombstones = {
        'Any': [],
        'Newbie': [],
        'Novice': [],
        'Seasoned': [],
        'Veteran': [],
        'Ported as Seasoned': [],
        'Ported as Veteran': []
    }
    num_deaths = 0
    for death in dead_characters:
        num_deaths = num_deaths + 1
        num_journals = Journal.objects.filter(game_attendance__attending_character=death.relevant_character).count()
        tombstone = {
            "death": death,
            "num_journals": num_journals,
        }
        tombstones[death.relevant_character.get_calculated_contractor_status_display()].append(tombstone)
    num_headers = Graveyard_Header.objects.all().count()
    if num_headers > 0:
        header = Graveyard_Header.objects.all()[randint(0,num_headers-1)].header
    else:
        header = "RIP"
    context = {
        'tombstones': tombstones,
        'character_deaths': dead_characters,
        'header': header,
        'num_deaths': num_deaths,
    }
    return render(request, 'characters/graveyard.html', context)

def view_artifact(request, artifact_id):
    artifact = get_object_or_404(Artifact, id=artifact_id)
    characters = [artifact.character] if artifact.character else []

    if artifact.crafting_character:
        characters.append(artifact.crafting_character)
    if characters and not [x for x in characters if x.player_can_view(request.user)]:
        raise PermissionDenied("You do not have permission to view this item")
    attribute_val_by_id = None
    ability_val_by_id = None

    if request.user.is_anonymous or not (request.user.is_superuser or request.user.profile.ps2_user or request.user.profile.early_access_user):
        raise PermissionDenied("You are not authorized to create a new power in this system.")

    if artifact.character:
        attribute_val_by_id = artifact.character.get_attribute_values_by_id()
        ability_val_by_id = artifact.character.get_ability_values_by_id()
    context = {
        "artifact": artifact,
        "attribute_value_by_id": attribute_val_by_id,
        "ability_value_by_id": ability_val_by_id,
    }
    return render(request, 'characters/view_artifact.html', context)


def view_character(request, character_id, secret_key=None):
    character = get_object_or_404(Character, id=character_id)
    if character.player and secret_key:
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character_id,)))
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Character")
    secret_key_valid = False
    if secret_key:
        secret_key_valid = character.is_editable_with_key(secret_key)
    else:
        secret_key = ""
    user_can_edit = (request.user.is_authenticated and character.player_can_edit(request.user)) or secret_key_valid
    early_access = request.user and hasattr(request.user, "profile") and request.user.profile.early_access_user
    if not character.stats_snapshot:
        context={"character": character,
                 "user_can_edit": user_can_edit}
        return render(request, 'characters/legacy_character.html', context)

    legacy_powers = character.power_full_set.filter(dice_system=SYS_LEGACY_POWERS).all()
    new_powers = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_NONE).all()
    crafting_artifact_gifts = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_ARTIFACT).all()
    crafting_consumable_gifts = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_CONSUMABLE).all()
    signature_item_gifts = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_SIGNATURE).all()

    char_ability_values = character.get_abilities()
    ability_value_by_id = {}
    char_value_ids = [x.relevant_ability.id for x in char_ability_values]
    primary_zero_values = [(x.name, x, 0) for x in Ability.objects.filter(is_primary=True).order_by("name").all()
                 if x.id not in char_value_ids]
    all_ability_values = []
    for x in char_ability_values:
        all_ability_values.append((x.relevant_ability.name, x.relevant_ability, x.value))
        ability_value_by_id[x.relevant_ability.id] = x.value
    ability_value_by_name = list(merge(primary_zero_values, all_ability_values))
    unspent_experience = character.unspent_experience()
    exp_earned = character.exp_earned()
    exp_cost = character.exp_cost()

    equipment_form = EquipmentForm()
    bio_form = BioForm()

    num_journal_entries = character.num_journals if character.num_journals else 0
    latest_journals = []
    if num_journal_entries > 0:
        journal_query = Journal.objects.filter(game_attendance__attending_character=character.id).order_by('-created_date')
        if request.user.is_anonymous or not request.user.profile.view_adult_content:
            journal_query = journal_query.exclude(is_nsfw=True)
        journals = journal_query.all()
        for journal in journals:
            if len(latest_journals) > 2:
                break
            if journal.player_can_view(request.user):
                latest_journals.append(journal)

    journal_cover = get_object_or_none(JournalCover, character=character.id)
    next_entry = get_characters_next_journal_credit(character) if user_can_edit else None

    available_gift = character.num_unspent_rewards() > 0
    circumstance_form = None
    condition_form = None
    artifact_form = None
    world_element_initial_cell = character.world_element_initial_cell()
    world_element_cell_choices = None
    default_scar_field = None
    if user_can_edit:
        # We only need these choices if the user can edit, both for forms and for char sheet.
        world_element_cell_choices = character.world_element_cell_choices()
        circumstance_form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)
        condition_form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)
        artifact_form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)
        default_scar_field = get_default_scar_choice_field()

    artifacts = get_world_element_default_dict(world_element_cell_choices)
    signature_items = []
    lost_signature_items = []
    for artifact in character.artifact_set.all():
        if hasattr(artifact, "cell") and artifact.cell:
            artifacts[artifact.cell].append(artifact)
        else:
            signature_items.append(artifact)
    for artifact in Artifact.objects.filter(crafting_character = character, is_signature=True).all():
        if artifact.character is not None and artifact.character != character:
            lost_signature_items.append(artifact)
    artifacts = dict(artifacts)

    circumstances = get_world_element_default_dict(world_element_cell_choices)
    for circumstance in character.circumstance_set.all():
        circumstances[circumstance.cell].append(circumstance)
    circumstances = dict(circumstances)

    conditions = get_world_element_default_dict(world_element_cell_choices)
    for condition in character.condition_set.all():
        conditions[condition.cell].append(condition)
    conditions = dict(conditions)

    assets = character.stats_snapshot.assetdetails_set.all()
    liabilities = character.stats_snapshot.liabilitydetails_set.all()
    attributes = character.get_attributes()
    attribute_value_by_id = {}
    for attr in attributes:
        attribute_value_by_id[attr.relevant_attribute.id] = attr.val_with_bonuses()
    context = {
        'character': character,
        'user_can_edit': user_can_edit,
        'early_access': early_access,
        'health_display': character.get_health_display(),
        'ability_value_by_name': ability_value_by_name,
        'ability_value_by_id': ability_value_by_id,
        'attributes': attributes,
        'attribute_value_by_id': attribute_value_by_id,
        'tutorial': get_object_or_404(CharacterTutorial),
        'battle_scar_form': BattleScarForm(),
        'default_scar_field': default_scar_field,
        'trauma_form': TraumaForm(prefix="trauma"),
        'injury_form': InjuryForm(request.POST, prefix="injury"),
        'exp_cost': exp_cost,
        'exp_earned': exp_earned,
        'unspent_experience': unspent_experience,
        'equipment_form': equipment_form,
        'bio_form': bio_form,
        'secret_key': secret_key,
        'secret_key_valid': secret_key_valid,
        'num_journal_entries': num_journal_entries,
        'journal_cover': journal_cover,
        'next_entry': next_entry,
        'latest_journals': latest_journals,
        'available_gift': available_gift,
        'circumstance_form': circumstance_form,
        'condition_form': condition_form,
        'artifact_form': artifact_form,
        'artifacts_by_cell': artifacts,
        'conditions_by_cell': conditions,
        'circumstances_by_cell': circumstances,
        'initial_cell': world_element_initial_cell,
        'assets': assets,
        'liabilities': liabilities,
        'weapons_by_type': get_weapons_by_type(),
        'legacy_powers': legacy_powers,
        'new_powers': new_powers,
        'crafting_artifact_gifts': crafting_artifact_gifts,
        'crafting_consumable_gifts': crafting_consumable_gifts,
        'signature_item_gifts': signature_item_gifts,
        'signature_items': signature_items,
        'lost_signature_items': lost_signature_items,
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
    assigned_powers = character.power_full_set.exclude(crafting_type=CRAFTING_SIGNATURE).all()
    unassigned_powers = request.user.power_full_set.filter(character=None, is_deleted=False).exclude(crafting_type=CRAFTING_SIGNATURE).order_by('-pub_date').all()
    assigned_items = character.get_signature_items()
    unassigned_items = character.player.artifact_set.filter(cell=None, is_signature=True, crafting_character__isnull=True).all()
    context = {
        'character': character,
        'assigned_powers': assigned_powers,
        'unassigned_powers': unassigned_powers,
        'assigned_items': assigned_items,
        'unassigned_items': unassigned_items,
    }
    return render(request, 'characters/choose_powers.html', context)


def toggle_item(request, character_id, sig_artifact_id):
    character = get_object_or_404(Character, id=character_id)
    sig_item = get_object_or_404(Artifact, id=sig_artifact_id)
    if not (character.player_can_edit(request.user)):
        raise PermissionDenied("You do not have permission to edit this Character")
    if not sig_item.is_signature:
        raise PermissionDenied("This isn't a signature item")
    for power in sig_item.power_full_set.all():
        if not power.player_can_edit(request.user):
            raise PermissionDenied("You do not have permission to edit a Gift on this item")
    if request.method == 'POST':
        assignment_form = ConfirmAssignmentForm(request.POST)
        if assignment_form.is_valid():
            with transaction.atomic():
                if sig_item.character == character:
                    # Unassign the item
                    sig_item.character = None
                    sig_item.crafting_character = None
                    sig_item.save()
                    for power in sig_item.power_full_set.all():
                        power.set_self_and_children_privacy(is_private=False)
                    for reward in sig_item.get_assigned_rewards():
                        reward.refund_keeping_character_assignment()
                elif not sig_item.character:
                    # Assign the item
                    sig_item.character = character
                    sig_item.crafting_character = character
                    sig_item.save()
                    for power_full in sig_item.power_full_set.all():
                        rewards_to_be_spent = character.reward_cost_for_power(power_full)
                        for reward in rewards_to_be_spent:
                            reward.assign_to_power(power_full.latest_revision())
                character.reset_attribute_bonuses()
            return HttpResponseRedirect(reverse('characters:characters_power_picker', args=(character.id,)))
    else:
        rewards_to_be_spent = character.reward_cost_for_item(sig_item)
        context = {
            'character': character,
            'item': sig_item,
            'assignment_form': ConfirmAssignmentForm(),
            'rewards_to_spend': rewards_to_be_spent["rewards_to_spend"],
            'gift_deficit': rewards_to_be_spent["gift_deficit"],
            'improvement_deficit': rewards_to_be_spent["improvement_deficit"],
            'item_cost': rewards_to_be_spent["item_cost"],
        }
        return render(request, 'characters/confirm_item_assignment.html', context)


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
                character.reset_attribute_bonuses()
            return HttpResponseRedirect(reverse('characters:characters_power_picker', args=(character.id,)))
        else:
            print(assignment_form.errors)
            return None
    else:
        rewards_to_be_spent = character.reward_cost_for_power(power_full)
        reward_deficit = power_full.get_gift_cost() - len(rewards_to_be_spent)
        insufficient_gifts = character.num_unspent_gifts() == 0
        context = {
            'character': character,
            'power_full': power_full,
            'assignment_form': ConfirmAssignmentForm(),
            'insufficient_gifts': insufficient_gifts,
            'reward_deficit': reward_deficit,
            'rewards_to_spend': rewards_to_be_spent,
        }
        return render(request, 'characters/confirm_power_assignment.html', context)

def view_character_contacts(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    contacts = get_character_contacts(character)
    context = {
        'character': character,
        'contacts': dict(contacts),
    }
    return render(request, 'characters/view_character_contacts.html', context)


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
            initial=[{"reward": x} for x in request.user.profile.get_avail_exp_rewards()])
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
            initial=[{"reward": x} for x in request.user.profile.get_avail_exp_rewards()])
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

def item_timeline(request, artifact_id):
    artifact = get_object_or_404(Artifact, id=artifact_id)
    if artifact.character and not artifact.character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this artifact")
    status_changes = list(artifact.artifactstatuschange_set.order_by("-created_time").all())
    transfers = list(artifact.artifacttransferevent_set.order_by("-created_time").all())

    events = list(merge(status_changes, transfers, key=lambda x: x.created_time, reverse=True))
    context = {
        "events": events,
    }
    return render(request, 'characters/item_timeline.html', context)


def character_timeline(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Character")

    assigned_rewards = [(x.assigned_on, "reward", x) for x in character.spent_rewards_rev_sort()]
    completed_games = [(x.relevant_game.end_time, "game", x) for x in character.completed_games_rev_sort()]
    character_edit_history = [(x.created_time, "edit", x) for x in
                              character.contractstats_set.filter(is_snapshot=False).order_by("-created_time").all()[:1]]
    exp_rewards = [(x.created_time, "exp_reward", x) for x in character.experiencereward_set.filter(is_void=False).order_by("-created_time").all()]
    events_by_date = list(merge(assigned_rewards, completed_games, character_edit_history, exp_rewards, reverse=True))
    timeline = defaultdict(list)
    for event in events_by_date:
        if event[1] == "edit":
            phrases = event[2].get_change_phrases()
            if len(phrases):
                timeline[event[0].strftime("%d %b %Y")].append((event[1], phrases))
        else:
            timeline[event[0].strftime("%d %b %Y")].append((event[1], event[2]))
    context = {
        'timeline': dict(timeline),
    }
    return render(request, 'characters/character_timeline.html', context)


def transfer_artifact(request, artifact_id):
    if request.method == "POST":
        artifact = get_object_or_404(Artifact, id=artifact_id)
        if not artifact.character:
            raise ValueError("Artifact has no character and cannot be transferred")
        __check_edit_perms(request, artifact.character)
        form = make_transfer_artifact_form(artifact.character, artifact.character.cell)(request.POST)
        if form.is_valid():
            with transaction.atomic():
                artifact = Artifact.objects.select_for_update().get(pk=artifact_id)
                artifact.transfer_to_character(
                    transfer_type=form.cleaned_data["transfer_type"],
                    to_character=form.cleaned_data["to_character"],
                    notes=form.cleaned_data["notes"] if "notes" in form.cleaned_data else "",)
    return HttpResponseRedirect(reverse('characters:characters_artifact_view', args=(artifact_id,)))


def post_scar(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        __check_edit_perms(request, character, secret_key)
        form = BattleScarForm(request.POST)
        if form.is_valid():
            battle_scar = BattleScar(description = form.cleaned_data['scar_description'],
                                     system = form.cleaned_data['scar_system'],
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
                character = Character.objects.select_for_update().get(pk=character.pk)
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
            character = Character.objects.select_for_update().get(pk=character.pk)
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

def dec_injury(request, injury_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        injury = get_object_or_404(Injury, id=injury_id)
        __check_edit_perms(request, injury.character, secret_key)
        new_sev = injury.severity - 1
        with transaction.atomic():
            if new_sev <= 0:
                injury.delete()
            else:
                injury.severity = new_sev
                injury.save()
        return JsonResponse({"severity": new_sev,
                             "stabilized": injury.is_stabilized}, status=200)
    return JsonResponse({"error": ""}, status=400)

def inc_injury(request, injury_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        injury = get_object_or_404(Injury, id=injury_id)
        __check_edit_perms(request, injury.character, secret_key)
        with transaction.atomic():
            injury.severity = injury.severity + 1
            injury.save()
        return JsonResponse({"severity": injury.severity,
                             "stabilized": injury.is_stabilized}, status=200)
    return JsonResponse({"error": ""}, status=400)

def stabilize_injury(request, injury_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        injury = get_object_or_404(Injury, id=injury_id)
        __check_edit_perms(request, injury.character, secret_key)
        with transaction.atomic():
            injury.is_stabilized = True
            injury.save()
        return JsonResponse({"severity": injury.severity,
                             "stabilized": injury.is_stabilized}, status=200)
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

def post_bio(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        form = BioForm(request.POST)
        __check_edit_perms(request, character, secret_key)
        if form.is_valid():
            character.background = form.cleaned_data['bio']
            with transaction.atomic():
                character.save()
            return JsonResponse({"bio": form.cleaned_data['bio']}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)

    return JsonResponse({"error": ""}, status=400)



def post_world_element(request, character_id, element, secret_key = None):
    if request.is_ajax and request.method == "POST":
        WorldElement = get_world_element_class_from_url_string(element)
        if not WorldElement:
            return JsonResponse({"error": "Invalid world element"}, status=400)
        character = get_object_or_404(Character, id=character_id)
        __check_edit_perms(request, character, secret_key)
        world_element_cell_choices = character.world_element_cell_choices()
        world_element_initial_cell = character.world_element_initial_cell()
        form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)(request.POST)
        if form.is_valid():
            new_element = WorldElement(
                character=character,
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                system=form.cleaned_data['system'],
                cell=form.cleaned_data['cell'],
            )
            with transaction.atomic():
                new_element.save()
            ser_instance = serializers.serialize('json', [new_element, ])
            return JsonResponse({"instance": ser_instance, "id": new_element.id, "cellId": new_element.cell.id}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": ""}, status=400)

def delete_world_element(request, element_id, element, secret_key = None):
    if request.is_ajax and request.method == "POST":
        WorldElement = get_world_element_class_from_url_string(element)
        if not WorldElement:
            return JsonResponse({"error": "Invalid world element"}, status=400)
        ext_element = get_object_or_404(WorldElement, id=element_id)
        character = ext_element.character
        __check_edit_perms(request, character, secret_key)
        if hasattr(ext_element, "is_signature") and ext_element.is_signature:
            raise ValueError("Cannot delete signature items")
        with transaction.atomic():
            ext_element.delete()
        return JsonResponse({}, status=200)
    return JsonResponse({"error": ""}, status=400)


def edit_world_element(request, element_id, element, secret_key=None):
    if request.is_ajax and request.method == "POST":
        WorldElement = get_world_element_class_from_url_string(element)
        if not WorldElement:
            return JsonResponse({"error": "Invalid world element"}, status=400)
        ext_element = get_object_or_404(WorldElement, id=element_id)
        character = ext_element.character
        __check_edit_perms(request, character, secret_key)
        world_element_cell_choices = character.world_element_cell_choices()
        world_element_initial_cell = character.world_element_initial_cell()
        form = make_world_element_form(world_element_cell_choices, world_element_initial_cell, for_new=False)(request.POST)
        if form.is_valid():
            with transaction.atomic():
                ext_element = WorldElement.objects.select_for_update().get(pk=ext_element.pk)
                ext_element.name = form.cleaned_data['name']
                ext_element.description = form.cleaned_data['description']
                if not hasattr(ext_element, "is_signature") or not ext_element.is_signature:
                    ext_element.system = form.cleaned_data['system']
                grey_out = None
                art_status = None
                if hasattr(ext_element, "most_recent_status_change") and ext_element.cell is None:
                    status_form = make_artifact_status_form(ext_element.most_recent_status_change)(request.POST)
                    if status_form.is_valid():
                        if "change_availability" in status_form.changed_data:
                            ext_element.change_availability(
                                status_type=status_form.cleaned_data["change_availability"],
                                notes=status_form.cleaned_data["notes"] if "notes" in status_form.cleaned_data else ""
                            )
                            grey_out = status_form.cleaned_data["change_availability"] in [LOST, DESTROYED]
                        else:
                            grey_out = ext_element.most_recent_status_change and ext_element.most_recent_status_change in [LOST, DESTROYED]
                    art_status = ext_element.most_recent_status_change
                ext_element.save()
            ser_instance = serializers.serialize('json', [ext_element, ])
            responseMap = {"instance": ser_instance,
                           "id": ext_element.id,
                           "grey_out": grey_out,
                           "artifact_status": art_status,
                           "cellId": ext_element.cell.id if ext_element.cell else None}
            return JsonResponse(responseMap, status=200)
        print(form.errors)
        return JsonResponse({}, status=200)
    return JsonResponse({"error": ""}, status=400)
