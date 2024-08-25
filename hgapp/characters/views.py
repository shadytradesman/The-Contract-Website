from random import randint
from datetime import timedelta
from heapq import merge

from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.views import View
from django.core import serializers
from collections import defaultdict
from django.forms import formset_factory
from django.contrib.auth import REDIRECT_FIELD_NAME
from account.utils import handle_redirect_to_login
from django.http import HttpResponseRedirect
from django.middleware.csrf import rotate_token
from django.templatetags.static import static
from django.template.loader import render_to_string
from notifications.models import Notification, CONTRACTOR_NOTIF


from characters.models import Character, BasicStats, Character_Death, Graveyard_Header, Attribute, Ability, \
    CharacterTutorial, Asset, Liability, BattleScar, Trauma, TraumaRevision, Injury, Source, ExperienceReward, Artifact, \
    LOST, DESTROYED, AT_HOME, CONDITION, CIRCUMSTANCE, TROPHY, TRAUMA,StockWorldElement, LooseEnd, LOOSE_END, CharacterImage
from powers.models import Power_Full, SYS_LEGACY_POWERS, SYS_PS2, CRAFTING_NONE, CRAFTING_SIGNATURE, CRAFTING_ARTIFACT, \
    CRAFTING_CONSUMABLE
from powers.signals import gift_major_revision
from characters.forms import make_character_form, CharacterDeathForm, ConfirmAssignmentForm, AttributeForm, get_ability_form, \
    AssetForm, LiabilityForm, BattleScarForm, TraumaForm, InjuryForm, SourceValForm, make_allocate_gm_exp_form, EquipmentForm,\
    DeleteCharacterForm, BioForm, make_world_element_form, get_default_scar_choice_form, make_artifact_status_form, \
    make_transfer_artifact_form, make_consumable_use_form, NotesForm, get_default_world_element_choice_form, \
    LooseEndForm, LooseEndDeleteForm, create_image_upload_form, DeleteImageForm
from characters.form_utilities import get_edit_context, character_from_post, update_character_from_post, \
    grant_trauma_to_character, delete_trauma_rev, get_world_element_class_from_url_string, get_blank_sheet_context
from characters.view_utilities import get_characters_next_journal_credit, get_world_element_default_dict, get_weapons_by_type, \
    does_character_have_outstanding_questions, next_question_reward


from journals.models import Journal, JournalCover
from cells.models import Cell
from images.models import PrivateUserImage

from hgapp.utilities import get_object_or_none

from games.game_utilities import get_character_contacts

def __check_world_element_perms(request, character, secret_key=None, ext_element=None):
    if character:
        try:
            __check_edit_perms(request, character, secret_key)
            return True
        except PermissionDenied:
            if hasattr(character, "cell") and character.cell.player_can_run_games(request.user):
                return True
        raise PermissionDenied("You do not have permission to edit this Character")
    if ext_element:
        return ext_element.creating_player == request.user
    else:
        raise ValueError("Checking world element perms requires a character or existing element")


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


def blank_sheet(request):
    context = get_blank_sheet_context()
    return render(request, 'characters/print_pages/blank/blank_sheet.html', context)


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
            if character.player is not None and character.player != request.user:
                Notification.objects.create(
                    user=character.player,
                    headline="Contractor edited",
                    content="{} edited {}".format(request.user.username, character.name),
                    url=reverse('characters:characters_view', args=(character.id,)),
                    notif_type=CONTRACTOR_NOTIF)
        url_args = (character.id,) if request.user.is_authenticated else (character.id, character.edit_secret_key,)
        return HttpResponseRedirect(reverse('characters:characters_view', args=url_args))
    else:
        rotate_token(request)  # Prevent interleaved edit form submissions.
        context = get_edit_context(user=request.user, existing_character=character, secret_key=secret_key)
        return render(request, 'characters/edit_pages/edit_character.html', context)


@login_required
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


@login_required
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
                    edited_death = obit_form.save()
                    if obit_form.cleaned_data['is_void']:
                        edited_death.mark_void()
            else:
                return None
        else:
            obit_form=CharacterDeathForm(request.POST)
            if obit_form.is_valid():
                new_character_death = obit_form.save(commit=False)
                new_character_death.relevant_character = character
                new_character_death.date_of_death = timezone.now()
                with transaction.atomic():
                    new_character_death.save()
                    character.is_dead = True
                    character.save()
                    if character.number_of_victories() > 0 and character.cell:
                        for membership in character.cell.get_unbanned_members():
                            Notification.objects.create(
                                user=membership.member_player,
                                headline="{} died".format(character.name),
                                content="{} victories, {} journals".format(character.number_of_victories(),
                                                                           character.num_journals),
                                url=reverse('characters:characters_view', args=(character.id,)),
                                notif_type=CONTRACTOR_NOTIF,
                                is_timeline=True,
                                article=new_character_death)
            else:
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
    dead_characters = Character_Death.objects\
        .select_related("relevant_character__player__profile")\
        .filter(is_void=False)\
        .filter(relevant_character__private=False)\
        .exclude(relevant_character__status='ANY') \
        .exclude(relevant_character__num_games=0) \
        .exclude(relevant_character__player__profile__is_private=True) \
        .order_by('-date_of_death')\
        .all()
    tombstones = {
        'Any': [],
        'Newbie': [],
        'Novice': [],
        'Seasoned': [],
        'Professional': [],
        'Veteran': [],
        'Ported Seasoned': [],
        'Ported Veteran': []
    }
    num_deaths = 0
    num_deaths_by_tier = defaultdict(int)
    for death in dead_characters:
        num_deaths = num_deaths + 1
        num_journals = death.relevant_character.num_journals
        tombstone = {
            "death": death,
            "num_journals": num_journals,
        }
        status = death.relevant_character.get_calculated_contractor_status_display()
        tombstones[status].append(tombstone)
        num_deaths_by_tier[status] += 1
    num_headers = Graveyard_Header.objects.all().count()
    if num_headers > 0:
        header = Graveyard_Header.objects.all()[randint(0,num_headers-1)].header
    else:
        header = "RIP"
    context = {
        'tombstones': tombstones,
        'character_deaths': dead_characters,
        'num_deaths_by_tier': num_deaths_by_tier,
        'header': header,
        'num_deaths': num_deaths,
        'early_access': request.user.is_authenticated and request.user.profile.early_access_user,
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

    if artifact.character:
        attribute_val_by_id = artifact.character.get_attribute_values_by_id()
        ability_val_by_id = artifact.character.get_ability_values_by_id()

    related_artifacts = []
    stock_gifts = []
    power = artifact.power_set.first()
    if power:
        related_artifacts = Artifact.objects\
            .filter(Q(is_crafted_artifact=True) | Q(is_signature=True))\
            .exclude(character__isnull=True)\
            .exclude(character__private=True).order_by('?')[:5]
        stock_gifts = Power_Full.objects\
            .filter(dice_system=SYS_PS2, tags__in=["example"], latest_rev__modality=power.modality_id)\
            .order_by('?')[:5]
    context = {
        "is_trophy": not (artifact.is_crafted_artifact or artifact.is_signature or artifact.is_consumable),
        "artifact": artifact,
        "attribute_value_by_id": attribute_val_by_id,
        "ability_value_by_id": ability_val_by_id,
        "stock_gifts": stock_gifts,
        "related_artifacts": related_artifacts,
    }
    return render(request, 'characters/view_artifact.html', context)


class CharacterArtifacts:
    artifacts = None
    signature_items = None
    lost_signature_items = None
    consumables = None
    avail_crafted_artifacts = None
    unavail_crafted_artifacts = None

    def __init__(self, character, world_element_cell_choices):
        self.signature_items = []
        self.lost_signature_items = []
        self.consumables = []
        self.avail_crafted_artifacts = []
        self.unavail_crafted_artifacts = []
        self.artifacts = get_world_element_default_dict(world_element_cell_choices)
        for artifact in character.artifact_set.exclude(is_deleted=True).all():
            if hasattr(artifact, "cell") and artifact.cell:
                self.artifacts[artifact.cell].append(artifact)
            elif artifact.is_signature:
                self.signature_items.append(artifact)
            elif artifact.is_consumable:
                self.consumables.append(artifact)
            elif artifact.is_crafted_artifact:
                if artifact.most_recent_status_change and artifact.most_recent_status_change in [LOST, AT_HOME,
                                                                                                 DESTROYED]:
                    self.unavail_crafted_artifacts.append(artifact)
                else:
                    self.avail_crafted_artifacts.append(artifact)

        for artifact in Artifact.objects.filter(crafting_character=character, is_signature=True,
                                                is_deleted=False).all():
            if artifact.character is not None and artifact.character != character:
                self.lost_signature_items.append(artifact)

def view_character_stock(request, character_id, secret_key=None):
    character = get_object_or_404(Character, id=character_id)
    character = Character.objects.filter(id=character.id).select_related("stats_snapshot").first()
    if character.player and secret_key:
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character_id,)))
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Contractor")
    secret_key_valid = False
    if secret_key:
        secret_key_valid = character.is_editable_with_key(secret_key)
    else:
        secret_key = ""
    user_can_edit = (request.user.is_authenticated and character.player_can_edit(request.user)) or secret_key_valid
    user_can_gm = character.player_can_gm(request.user)

    legacy_powers = character.power_full_set.filter(dice_system=SYS_LEGACY_POWERS).all()
    new_powers = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_NONE).select_related("latest_rev__modality").select_related("latest_rev__vector").select_related("latest_rev__base").all()
    crafting_artifact_gifts = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_ARTIFACT).select_related("latest_rev__modality").select_related("latest_rev__vector").select_related("latest_rev__base").all()
    crafting_consumable_gifts = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_CONSUMABLE).select_related("latest_rev__modality").select_related("latest_rev__vector").select_related("latest_rev__base").all()
    equipment_form = EquipmentForm()

    artifact_form = None
    default_trophy_form = None
    world_element_cell_choices = None
    condition_form = None

    world_element_initial_cell = character.world_element_initial_cell()
    if user_can_edit or user_can_gm:
        world_element_cell_choices = character.world_element_cell_choices()
        condition_form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)
        artifact_form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)
        default_trophy_form = get_default_world_element_choice_form(TROPHY)

    char_artifacts = CharacterArtifacts(character, world_element_cell_choices)
    artifacts = dict(char_artifacts.artifacts)

    context = {
        'user_can_edit': user_can_edit,
        'user_can_gm': user_can_gm,
        'character': character,
        'equipment_form': equipment_form,
        'artifact_form': artifact_form,
        'artifacts_by_cell': artifacts,
        'legacy_powers': legacy_powers,
        'new_powers': new_powers,
        'crafting_artifact_gifts': crafting_artifact_gifts,
        'crafting_consumable_gifts': crafting_consumable_gifts,
        'signature_items': char_artifacts.signature_items,
        'consumables': char_artifacts.consumables,
        'avail_crafted_artifacts': char_artifacts.avail_crafted_artifacts,
        'unavail_crafted_artifacts': char_artifacts.unavail_crafted_artifacts,
        'default_trophy_form': default_trophy_form,
        'weapons_by_type': get_weapons_by_type(),
        'lost_signature_items': char_artifacts.lost_signature_items,
        'condition_form': condition_form,
    }
    return render(request, 'characters/view_pages/tab_stock.html', context)

def view_character(request, character_id, secret_key=None):
    character = get_object_or_404(Character, id=character_id)
    character = Character.objects.filter(id=character.id).select_related("stats_snapshot").first()
    if character.player and secret_key:
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character_id,)))
    if not character.player_can_view(request.user):
        if request.user.is_anonymous:
            return handle_redirect_to_login(request, redirect_field_name=REDIRECT_FIELD_NAME)
        raise PermissionDenied("You do not have permission to view this Contractor")
    secret_key_valid = False
    if secret_key:
        secret_key_valid = character.is_editable_with_key(secret_key)
    else:
        secret_key = ""
    user_can_edit = (request.user.is_authenticated and character.player_can_edit(request.user)) or secret_key_valid
    user_can_gm = character.player_can_gm(request.user)
    user_posts_moves = (request.user.is_authenticated and character.cell) \
                       and not (request.user == character.player) \
                       and (character.cell.player_can_post_world_events(request.user)
                            and character.cell.player_can_run_games(request.user)) \

    if not character.stats_snapshot:
        context={"character": character,
                 "user_can_edit": user_can_edit}
        return render(request, 'characters/legacy_character.html', context)

    ability_value_by_name, ability_value_by_id = character.get_abilities_by_name_and_id()
    unspent_experience = character.unspent_experience()
    exp_earned = character.exp_earned()
    exp_cost = character.exp_cost()

    bio_form = BioForm()

    num_journal_entries = character.num_journals if character.num_journals else 0
    latest_journals = []
    if num_journal_entries > 0:
        journal_query = Journal.objects.select_related("game_attendance__attending_character").filter(game_attendance__attending_character=character.id).order_by('-created_date')
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
    has_outstanding_question = does_character_have_outstanding_questions(character)

    num_spent_rewards = character.num_active_spent_rewards()
    num_total_rewards = character.num_active_rewards()
    character_at_reward_limit = character.effective_victories() > 1 and (2 * character.effective_victories()) == num_spent_rewards
    character_over_reward_limit = character.effective_victories() > 1 and (2 * character.effective_victories()) < num_spent_rewards
    num_unspent_rewards = character.num_unspent_rewards()
    available_gift = num_unspent_rewards > 0

    circumstance_form = None
    condition_form = None
    world_element_initial_cell = character.world_element_initial_cell()
    world_element_cell_choices = None
    default_scar_field = None
    default_condition_form = None
    default_circumstance_form = None
    default_trauma_form = None
    element_description_by_name = None
    if user_can_edit or user_can_gm:
        # We only need these choices if the user can edit, both for forms and for char sheet.
        world_element_cell_choices = character.world_element_cell_choices()
        circumstance_form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)
        condition_form = make_world_element_form(world_element_cell_choices, world_element_initial_cell)
        default_scar_field = get_default_scar_choice_form()
        default_condition_form = get_default_world_element_choice_form(CONDITION)
        default_circumstance_form = get_default_world_element_choice_form(CIRCUMSTANCE)
        default_trauma_form = get_default_world_element_choice_form(TRAUMA)
        element_descriptions = StockWorldElement.objects.filter(is_user_created=False).values_list('name', 'description')
        element_description_by_name = {x[0]: x[1] for x in element_descriptions}

    circumstances = get_world_element_default_dict(world_element_cell_choices)
    for circumstance in character.circumstance_set.select_related("cell").exclude(is_deleted=True).all():
        cell = circumstance.cell if circumstance.cell else character.cell
        circumstances[cell].append(circumstance)
    circumstances = dict(circumstances)
    deleted_but_not_bought_off_circumstances \
        = [x for x in character.circumstance_set.filter(cell__isnull=True, is_deleted=True, deleted_by_quirk_removal=False).all() \
            if x.record_of_quirk_grant()]

    conditions = get_world_element_default_dict(world_element_cell_choices)
    for condition in character.condition_set.select_related("cell").exclude(is_deleted=True).all():
        conditions[condition.cell].append(condition)
    conditions = dict(conditions)
    deleted_but_not_bought_off_conditions \
        = [x for x in character.condition_set.filter(cell__isnull=True, is_deleted=True, deleted_by_quirk_removal=False).all() \
           if x.record_of_quirk_grant()]

    assets = character.stats_snapshot.assetdetails_set.select_related("relevant_asset").all()
    liabilities = character.stats_snapshot.liabilitydetails_set.select_related("relevant_liability").all()
    attributes = character.get_attributes()
    attribute_value_by_id = {}
    for attr in attributes:
        attribute_value_by_id[attr.relevant_attribute.id] = attr.val_with_bonuses()

    moves = character.move_set.order_by("-created_date").all()
    loose_ends = character.looseend_set.filter(is_deleted=False).order_by("cutoff").all()
    expired_loose_ends = character.looseend_set.filter(is_deleted=False, cutoff=0).exists()
    unspent_exp = character.unspent_experience()
    num_questions_answered = character.answer_set.filter(is_valid=True).count()
    context = {
        'character': character,
        'num_mind_levels': character.num_mind_levels(),
        'num_body_levels': character.num_body_levels(),
        'unspent_exp': unspent_exp,
        'user_can_edit': user_can_edit,
        'user_can_gm': user_can_gm,
        'user_posts_moves': user_posts_moves,
        'health_display': character.get_health_display(),
        'ability_value_by_name': ability_value_by_name,
        'ability_value_by_id': ability_value_by_id,
        'attributes': attributes,
        'attribute_value_by_id': attribute_value_by_id,
        'tutorial': get_object_or_404(CharacterTutorial),
        'battle_scar_form': BattleScarForm(),
        'default_scar_field': default_scar_field,
        'element_description_by_name': element_description_by_name,
        'default_condition_form': default_condition_form,
        'default_circumstance_form': default_circumstance_form,
        'default_trauma_form': default_trauma_form,
        'trauma_form': TraumaForm(prefix="trauma"),
        'injury_form': InjuryForm(request.POST, prefix="injury"),
        'exp_cost': exp_cost,
        'exp_earned': exp_earned,
        'unspent_experience': unspent_experience,
        'bio_form': bio_form,
        'notes_form': NotesForm(),
        'secret_key': secret_key,
        'secret_key_valid': secret_key_valid,
        'num_journal_entries': num_journal_entries,
        'journal_cover': journal_cover,
        'next_entry': next_entry,
        'has_available_questions': has_outstanding_question,
        'next_question_reward': next_question_reward(character) if has_outstanding_question else None,
        'num_questions_answered': num_questions_answered,
        'last_few_answers': character.answer_set.filter(is_valid=True).order_by("-created_date")[:3] if num_questions_answered else [],
        'latest_journals': latest_journals,
        'available_gift': available_gift,
        'circumstance_form': circumstance_form,
        'condition_form': condition_form,
        'conditions_by_cell': conditions,
        'circumstances_by_cell': circumstances,
        'trouble_circumstances': deleted_but_not_bought_off_circumstances,
        'trouble_conditions': deleted_but_not_bought_off_conditions,
        'initial_cell': world_element_initial_cell,
        'assets': assets,
        'liabilities': liabilities,
        'num_improvements': character.num_improvements() if character.player == request.user else None,
        'num_gifts': character.num_gifts() if character.player == request.user else None,
        'num_spent_rewards': num_spent_rewards,
        'num_unspent_rewards': num_unspent_rewards,
        'num_total_rewards': num_total_rewards,
        'character_at_reward_limit': character_at_reward_limit,
        'character_over_reward_limit': character_over_reward_limit,
        'moves': moves,
        'num_moves':  moves.count(),
        'loose_ends': loose_ends,
        'expired_loose_ends': expired_loose_ends,
        'early_access': request.user.is_authenticated and request.user.profile.early_access_user,
    }
    return render(request, 'characters/view_pages/view_character.html', context)


def print_character(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Character")
    new_powers = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_NONE).all()
    crafting_artifact_gifts = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_ARTIFACT).all()
    crafting_consumable_gifts = character.power_full_set.filter(dice_system=SYS_PS2, crafting_type=CRAFTING_CONSUMABLE).all()
    mid_powers = new_powers.count() // 2
    char_artifacts = CharacterArtifacts(character, None)
    context = {
        "character": character,
        "character_blob": character.to_print_blob(),
        'new_powers_1': new_powers[mid_powers:],
        'new_powers_2': new_powers[:mid_powers],
        'crafting_artifact_gifts': crafting_artifact_gifts,
        'crafting_consumable_gifts': crafting_consumable_gifts,
        'artifacts': char_artifacts,
        "d10_outline_url": static("overrides/branding/d10-outline2.svg"),
        "d10_filled_url": static("overrides/branding/d10-filled.svg"),
        "timeline": character_timeline_str(request, character_id),
    }
    return render(request, 'characters/print_pages/print_character.html', context)


def archive_character(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Character")
    return HttpResponse(character.archive_txt(), content_type='text/plain; charset=UTF-8')


@login_required
def choose_powers(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if request.user.is_anonymous or not character.player_can_edit(request.user):
        raise PermissionDenied("You do not have permission to edit this Character")
    assigned_powers = character.power_full_set.exclude(crafting_type=CRAFTING_SIGNATURE).all()
    unassigned_powers = request.user.power_full_set.filter(character=None, is_deleted=False).exclude(crafting_type=CRAFTING_SIGNATURE).order_by('-pub_date').all()
    assigned_items = character.get_signature_items_crafted()
    unassigned_items = Artifact.objects.filter(creating_player=character.player, cell=None, is_signature=True, is_deleted=False, crafting_character__isnull=True)
    context = {
        'character': character,
        'assigned_powers': assigned_powers,
        'unassigned_powers': unassigned_powers,
        'assigned_items': assigned_items,
        'unassigned_items': unassigned_items,
    }
    return render(request, 'characters/choose_powers.html', context)


@login_required
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
                if sig_item.crafting_character == character:
                    # Unassign the item
                    if sig_item.character == character:
                        sig_item.character = None
                    sig_item.crafting_character = None
                    sig_item.save()
                    for power in sig_item.power_full_set.all():
                        if power.character == character:
                            # Unassign the power
                            power.character = None
                        power.save()
                        power.set_self_and_children_privacy(is_private=False)
                    for reward in sig_item.get_assigned_rewards():
                        reward.refund_keeping_character_assignment()
                elif not sig_item.crafting_character:
                    # Assign the item
                    if not sig_item.character:
                        sig_item.character = character
                    sig_item.crafting_character = character
                    sig_item.save()
                    for power_full in sig_item.power_full_set.all():
                        power_full.character = character
                        power_full.save()
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


@login_required
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
                    gift_major_revision.send(sender=Character.__class__,
                                             old_power="we don't use this",
                                             new_power=power_full.latest_rev,
                                             power_full=power_full)
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
                    if power_full.crafting_type in [CRAFTING_ARTIFACT, CRAFTING_CONSUMABLE]:
                        character.crafting_avail = True
                        character.highlight_crafting = True
                        character.save()
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


@login_required
def spend_reward(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_edit(request.user):
        raise PermissionDenied("You do not have permission to edit this Character")
    unassigned_powers = request.user.power_full_set.filter(is_deleted=False, character__isnull=True).all()
    unspent_exp = character.spendable_experience()
    num_spent_rewards = character.num_active_spent_rewards()
    num_total_rewards = character.num_active_rewards()
    character_at_reward_limit = character.effective_victories() > 1 and (2 * character.effective_victories()) == num_spent_rewards
    character_over_reward_limit = character.effective_victories() > 1 and (2 * character.effective_victories()) < num_spent_rewards
    context = {
        'character': character,
        'unassigned_powers': unassigned_powers,
        'unspent_exp': unspent_exp,
        'num_spent_rewards': num_spent_rewards,
        'num_total_rewards': num_total_rewards,
        'character_at_reward_limit': character_at_reward_limit,
        'character_over_reward_limit': character_over_reward_limit,
        'num_unspent_rewards': character.num_unspent_rewards(),
    }
    return render(request, 'characters/reward_character.html', context)


@login_required
def allocate_gm_exp(request, secret_key = None):
    valid_character_ids = [char.id for char in request.user.character_set.filter(is_deleted=False).all() if char.can_get_bonus_exp()]
    queryset = Character.objects.filter(id__in=valid_character_ids)
    RewardForm = make_allocate_gm_exp_form(queryset)
    RewardFormset = formset_factory(RewardForm, extra=0)
    if request.method == 'POST':
        reward_formset = RewardFormset(
            request.POST,
            initial=[{"reward": x} for x in request.user.profile.get_avail_exp_rewards()])
        if reward_formset.is_valid():
            for form in reward_formset:
                with transaction.atomic():
                    user = User.objects.select_for_update().get(pk=request.user.id) # for locking
                    reward = get_object_or_404(ExperienceReward, id=form.cleaned_data["reward_id"])
                    if reward.rewarded_character or reward.rewarded_player != request.user:
                        raise PermissionDenied("This reward has been allocated, or it isn't yours")
                    if "chosen_character" in form.changed_data:
                        char = form.cleaned_data["chosen_character"]
                        if char.player != request.user:
                            raise PermissionDenied("You cannot give your rewards to other people's characters!")
                        if not char.can_get_bonus_exp():
                            continue
                        reward.rewarded_character = char
                        reward.created_time = timezone.now()
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



@method_decorator(login_required(login_url='account_login'), name='dispatch')
class EnterLooseEnd(View):
    form_class = LooseEndForm
    template_name = 'characters/loose_ends/edit_loose_end.html'
    initial = None
    loose_end = None
    cell = None
    character = None

    def dispatch(self, *args, **kwargs):
        redirect = self.__check_permissions()
        if redirect:
            return redirect
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if not self.loose_end:
                    self.loose_end = LooseEnd(
                        character=self.character,
                        cell=self.character.cell,
                        granting_gm=self.request.user,
                        original_cutoff=form.cleaned_data["cutoff"]
                    )
                    Notification.objects.create(
                        user=self.character.player,
                        headline="New Loose End",
                        content="{} gave {} a Loose End".format(request.user.username, self.character.name),
                        url=reverse('characters:characters_view', args=(self.character.id,)),
                        notif_type=CONTRACTOR_NOTIF)
                self.loose_end.name = form.cleaned_data["name"]
                self.loose_end.description = form.cleaned_data["details"]
                self.loose_end.system = form.cleaned_data["threat"]
                self.loose_end.cutoff = form.cleaned_data["cutoff"]
                self.loose_end.threat_level = form.cleaned_data["threat_level"]
                self.loose_end.how_to_tie_up = form.cleaned_data["how_to_tie_up"]
                self.loose_end.save()
            return HttpResponseRedirect(reverse('characters:characters_view', args=(self.character.id,)))
        raise ValueError("Invalid loose end form")

    def __check_permissions(self):
        if not self.character.cell:
            raise PermissionDenied("Contractors must be a part of a Playgroup to have Loose Ends.")
        if not self.character.player_can_gm(self.request.user):
            raise PermissionDenied("You must have permissions to run Contracts in this Contractor's Playgroup to assign Loose Ends.")
        if self.character.player == self.request.user:
            raise PermissionDenied("You cannot edit your own loose ends")

    def __get_context_data(self):
        context = {
            'character': self.character,
            'loose_end': self.loose_end,
            'form': self.form_class(initial=self.initial),
            'stock_loose_end': get_default_world_element_choice_form(LOOSE_END),
        }
        return context


class CreateLooseEnd(EnterLooseEnd):

    def dispatch(self, *args, **kwargs):
        self.character = get_object_or_404(Character, id=self.kwargs['character_id'])
        self.cell = self.character.cell
        return super().dispatch(*args, **kwargs)


class EditLooseEnd(EnterLooseEnd):

    def dispatch(self, *args, **kwargs):
        self.loose_end = get_object_or_404(LooseEnd, id=self.kwargs['loose_end_id'])
        self.character = self.loose_end.character
        self.cell = self.loose_end.cell
        self.initial = {
            "name": self.loose_end.name,
            "details": self.loose_end.description,
            "cutoff": self.loose_end.cutoff,
            "threat": self.loose_end.system,
            "threat_level": self.loose_end.threat_level,
            "how_to_tie_up": self.loose_end.how_to_tie_up,
        }
        return super().dispatch(*args, **kwargs)


def delete_loose_end(request, loose_end_id):
    loose_end = get_object_or_404(LooseEnd, id=loose_end_id)
    character = loose_end.character
    if not character.cell:
        raise PermissionDenied("Contractors must be a part of a Playgroup to have Loose Ends.")
    if not character.player_can_gm(request.user):
        raise PermissionDenied(
            "You must have permissions to run Contracts in this Contractor's Playgroup to assign Loose Ends.")
    if character.player == request.user:
        raise PermissionDenied("You cannot resolve your own loose ends")
    if loose_end.is_deleted:
        raise ValueError("cannot end an already ended loose end")
    if request.method == "POST":
        form = LooseEndDeleteForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                loose_end = LooseEnd.objects.select_for_update().get(pk=loose_end.id)
                loose_end.deletion_reason = form.cleaned_data["resolution"]
                loose_end.is_deleted = True
                loose_end.deleted_date = timezone.now()
                loose_end.save()
        else:
            raise ValueError("Invalid loose end form")
        return HttpResponseRedirect(reverse('characters:characters_view', args=(character.id,)))
    form = LooseEndDeleteForm()
    context = {
        "character": character,
        "loose_end": loose_end,
        "form": form,
    }
    return render(request, 'characters/loose_ends/delete_loose_end.html', context)

#####
# View Character AJAX
####


def item_timeline(request, artifact_id):
    artifact = get_object_or_404(Artifact, id=artifact_id)
    if artifact.character and not artifact.character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this artifact")
    status_changes = list(artifact.artifactstatuschange_set.order_by("-created_time").all())
    transfers = list(artifact.artifacttransferevent_set.order_by("-created_time").all())
    timeline_events = artifact.artifacttimelineevent_set.order_by("-created_time").all()
    events = list(merge(status_changes, transfers, timeline_events, key=lambda x: x.created_time, reverse=True))
    context = {
        "events": events,
        "artifact": artifact,
    }
    return render(request, 'characters/item_timeline.html', context)


class CraftingTimelineBlock:
    crafting_events = None
    total_exp_spent = None
    total_crafted_consumables = None
    power_quantity = None
    scenario_name = None

    def __init__(self, crafting_events):
        self.crafting_events = crafting_events
        self.total_exp_spent_consumables = 0
        self.total_exp_spent_artifacts = 0
        self.total_crafted_consumables = 0
        self.power_quantity = []
        self.powers_by_artifact = defaultdict(list)
        self.total_art_effects_crafted = 0
        self.total_art_effects_free = 0
        if len(crafting_events) > 0:
            event = crafting_events[0]
            if event.relevant_attendance is not None:
                self.scenario_name = event.relevant_attendance.relevant_game.scenario.title
        for event in crafting_events:
            if event.relevant_power.modality.crafting_type == CRAFTING_CONSUMABLE:
                self.total_exp_spent_consumables += event.total_exp_spent
                total_made = 0
                total_free = 0
                for artifact_crafting in event.craftedartifact_set.all():
                    total_made += artifact_crafting.quantity
                    total_free += artifact_crafting.quantity_free
                self.total_crafted_consumables += total_made
                self.power_quantity.append({
                    "power": event.relevant_power,
                    "quantity": total_made,
                    "quantity_free": total_free
                })
            if event.relevant_power.modality.crafting_type == CRAFTING_ARTIFACT:
                self.total_exp_spent_artifacts += event.total_exp_spent
                for artifact_crafting in event.craftedartifact_set.all():
                    self.powers_by_artifact[artifact_crafting.relevant_artifact].append((event.relevant_power, artifact_crafting.quantity_free > 0))
                    self.total_art_effects_crafted += artifact_crafting.quantity
                    self.total_art_effects_free += artifact_crafting.quantity_free
        self.powers_by_artifact = dict(self.powers_by_artifact)


def character_timeline(request, character_id):
    context = timeline_context(character_id, request)
    return render(request, 'characters/character_timeline.html', context)


def character_timeline_str(request, character_id):
    context = timeline_context(character_id, request)
    return render_to_string('characters/character_timeline.html', context, request)


def timeline_context(character_id, request):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_view(request.user):
        raise PermissionDenied("You do not have permission to view this Character")
    assigned_rewards = [(x.assigned_on, "reward", x) for x in character.spent_rewards_rev_sort()]
    completed_games = [(x.relevant_game.end_time, "game", x) for x in character.completed_games_rev_sort()]
    condition_creation = [(x.created_time, "elem_created", x) for x in
                          character.condition_set.order_by("-created_time")]
    condition_deletion = [(x.deleted_date, "elem_deleted", x) for x in
                          character.condition_set.filter(is_deleted=True).order_by("-deleted_date")]
    circumstance_creation = [(x.created_time, "elem_created", x) for x in
                             character.circumstance_set.order_by("-created_time")]
    circumstance_deletion = [(x.deleted_date, "elem_deleted", x) for x in
                             character.circumstance_set.filter(is_deleted=True).order_by("-deleted_date")]
    craftings = character.craftingevent_set.order_by("-relevant_attendance__relevant_game__end_time").all()
    crafting_tuples = []
    if craftings:
        current_crafting_list = []
        last_attendance_examined = craftings[0].relevant_attendance
        first_craft_before_contract = False
        if last_attendance_examined is not None:
            craft_time = last_attendance_examined.relevant_game.end_time + timedelta(seconds=9)
        else:
            craft_time = character.pub_date + timedelta(seconds=9)
            first_craft_before_contract = True
        for crafting in craftings:
            if last_attendance_examined != crafting.relevant_attendance:
                crafting_tuples.append(
                    (craft_time,
                     "crafting",
                     CraftingTimelineBlock(current_crafting_list))
                )
                current_crafting_list = []
                last_attendance_examined = crafting.relevant_attendance
                craft_time = last_attendance_examined.relevant_game.end_time + timedelta(seconds=9)
            current_crafting_list.append(crafting)
        crafting_tuples.append(
            (
                craft_time,
                "crafting",
                CraftingTimelineBlock(current_crafting_list))
        )
        if len(crafting_tuples) > 0 and first_craft_before_contract:
            last = crafting_tuples.pop(0)
            crafting_tuples.append(last)
    character_edit_history = [(x.created_time, "edit", x) for x in
                          character.contractstats_set.filter(is_snapshot=False).order_by("-created_time").all()]
    character_edit_history = character_edit_history[:-1]
    exp_rewards = [(x.created_time + timedelta(seconds=2), "exp_reward", x) for x in
                   character.experiencereward_set.filter(is_void=False).order_by("-created_time").all()]
    moves = [(x.created_date, "move", x) for x in character.move_set.order_by("-created_date").all()]
    loose_ends = [(x.created_time, "elem_created", x) for x in character.looseend_set.order_by("-created_time").all()]
    loose_end_deleted = [(x.deleted_date, "elem_deleted", x) for x in
                         character.looseend_set.filter(is_deleted=True).order_by("-created_time").all()]
    events_by_date = list(merge(assigned_rewards,
                                completed_games,
                                condition_creation,
                                condition_deletion,
                                circumstance_creation,
                                circumstance_deletion,
                                loose_ends,
                                loose_end_deleted,
                                character_edit_history,
                                exp_rewards,
                                crafting_tuples,
                                moves,
                                reverse=True))
    timeline = defaultdict(list)
    for event in events_by_date:
        if event[1] == "edit":
            phrases = event[2].get_change_phrases()
            if len(phrases):
                timeline[event[0].strftime("%d %b %Y")].append((event[1], phrases, event[0].strftime("%d %b %H:%M")))
        else:
            timeline[event[0].strftime("%d %b %Y")].append((event[1], event[2], event[0].strftime("%d %b %H:%M")))
    context = {
        'timeline': dict(timeline),
    }
    return context


def use_consumable(request, artifact_id):
    if request.method == "POST":
        artifact = get_object_or_404(Artifact, id=artifact_id)
        if not artifact.character:
            raise ValueError("Artifact has no character and cannot be transferred")
        __check_edit_perms(request, artifact.character)
        form = make_consumable_use_form(artifact)(request.POST)
        if form.is_valid():
            with transaction.atomic():
                artifact = Artifact.objects.select_for_update().get(pk=artifact_id)
                artifact.quantity = form.cleaned_data["new_quantity"]
                artifact.save()
            return JsonResponse({"new_quantity": form.cleaned_data["new_quantity"]}, status=200)
        print(form.errors)
    return JsonResponse({"error": ""}, status=400)


def transfer_artifact(request, artifact_id):
    artifact = get_object_or_404(Artifact, id=artifact_id)
    start_char = artifact.character
    if request.method == "POST":
        __check_world_element_perms(request, character=artifact.character, ext_element=Artifact)
        max_quantity = 0
        if artifact.is_consumable:
            max_quantity = artifact.quantity
        form = make_transfer_artifact_form(start_char, start_char.cell if start_char else None, max_quantity, request.user)(request.POST)
        if form.is_valid():
            with transaction.atomic():
                artifact = Artifact.objects.select_for_update().get(pk=artifact_id)
                artifact.transfer_to_character(
                    transfer_type=form.cleaned_data["transfer_type"],
                    to_character=form.cleaned_data["to_character"],
                    notes=form.cleaned_data["notes"] if "notes" in form.cleaned_data else "",
                    quantity=form.cleaned_data["quantity"] if artifact.is_consumable else 1)
        else:
            raise ValueError("Invalid artifact transfer form")
            print(form.errors)
    if artifact.is_signature:
        return HttpResponseRedirect(reverse('characters:characters_artifact_view', args=(artifact_id,)))
    else:
        return HttpResponseRedirect(reverse('characters:characters_view', args=(start_char.pk,)))


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
                character = Character.objects.select_for_update(nowait=True).get(pk=character.pk)
                trauma_rev = grant_trauma_to_character(form, character)
            return JsonResponse({"id": trauma_rev.id,
                                 "system": trauma_rev.relevant_trauma.description,
                                 "name": trauma_rev.relevant_trauma.name},
                                status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)
    return JsonResponse({"error": ""}, status=400)


def delete_trauma(request, trauma_rev_id, used_xp, secret_key = None):
    if request.is_ajax and request.method == "POST":
        trauma_rev = get_object_or_404(TraumaRevision, id=trauma_rev_id)
        character = trauma_rev.relevant_stats.assigned_character
        __check_edit_perms(request, character, secret_key)
        with transaction.atomic():
            character = Character.objects.select_for_update(nowait=True).get(pk=character.pk)
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


def post_notes(request, character_id, secret_key = None):
    if request.is_ajax and request.method == "POST":
        character = get_object_or_404(Character, id=character_id)
        form = NotesForm(request.POST)
        __check_edit_perms(request, character, secret_key)
        if form.is_valid() and request.user != character.player:
            character.notes = form.cleaned_data['notes']
            with transaction.atomic():
                character.save()
            return JsonResponse({"notes": form.cleaned_data['notes']}, status=200)
        else:
            return JsonResponse({"error": form.errors}, status=400)

    return JsonResponse({"error": ""}, status=400)


def post_world_element(request, character_id, element, secret_key = None):
    if request.is_ajax and request.method == "POST":
        WorldElement = get_world_element_class_from_url_string(element)
        if not WorldElement:
            return JsonResponse({"error": "Invalid world element"}, status=400)
        character = get_object_or_404(Character, id=character_id)
        __check_world_element_perms(request, character, secret_key)
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
                granting_gm=request.user,
            )
            with transaction.atomic():
                new_element.save()
                if request.user != character.player:
                    Notification.objects.create(
                        user=character.player,
                        headline="New {}".format(new_element.get_type_display()),
                        content="{} gave {} a {}".format(request.user.username, character.name, new_element.get_type_display()),
                        url=reverse('characters:characters_view', args=(character.id,)),
                        notif_type=CONTRACTOR_NOTIF)
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
        __check_world_element_perms(request, character, secret_key)
        if hasattr(ext_element, "is_signature") and ext_element.is_signature:
            raise ValueError("Cannot delete signature items")
        with transaction.atomic():
            ext_element.mark_deleted("Removed by {}".format(request.user.username))
        return JsonResponse({}, status=200)
    return JsonResponse({"error": ""}, status=400)


def edit_world_element(request, element_id, element, secret_key=None):
    if request.is_ajax and request.method == "POST":
        WorldElement = get_world_element_class_from_url_string(element)
        if not WorldElement:
            return JsonResponse({"error": "Invalid world element"}, status=400)
        ext_element = get_object_or_404(WorldElement, id=element_id)
        character = ext_element.character
        __check_world_element_perms(request, character, secret_key, ext_element)
        world_element_cell_choices = character.world_element_cell_choices() if character else None
        world_element_initial_cell = character.world_element_initial_cell() if character else None
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
        return JsonResponse({}, status=200)
    return JsonResponse({"error": ""}, status=400)


@login_required
def upload_image(request, character_id):
    character = get_object_or_404(Character, id=character_id)
    if not request.user.is_authenticated:
        raise PermissionDenied("Logged in only")
    if not character.player_can_edit(request.user):
        raise PermissionDenied("This Contractor has been deleted, or you're not allowed to edit it")

    if request.method == 'POST':
        form = create_image_upload_form(character)(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                if character.images.count() == 0:
                    is_primary=True
                else:
                    is_primary=form.cleaned_data["is_primary"]
                new_image = PrivateUserImage.objects.create(
                    image=request.FILES['file'],
                    uploader=request.user,
                )
                character.images.add(new_image)
                if is_primary:
                    character.primary_image = new_image
                    character.save()
        else:
            raise ValueError("Invalid image upload form")
    upload_form = create_image_upload_form(character)
    images = character.images.exclude(is_deleted=True).all()
    context = {
        "character": character,
        "upload_form": upload_form,
        "delete_form": DeleteImageForm(),
        "images": images,
    }
    return render(request, 'characters/manage_images.html', context)


@login_required
def delete_image(request, character_id, image_id):
    character = get_object_or_404(Character, id=character_id)
    if not request.user.is_authenticated:
        raise PermissionDenied("Logged in only")
    if not character.player_can_edit(request.user):
        raise PermissionDenied("This Contractor has been deleted, or you're not allowed to edit it")
    character_image = get_object_or_404(CharacterImage, relevant_character=character_id, relevant_image=image_id)
    image = character_image.relevant_image
    if request.method == 'POST':
        form = DeleteImageForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                character.images.remove(image)
                if character.primary_image == image:
                    character.primary_image = character.images.first()
                    character.save()
    return HttpResponseRedirect(reverse('characters:characters_upload_image', args=(character_id,)))

@login_required
def make_primary_image(request, character_id, image_id):
    character = get_object_or_404(Character, id=character_id)
    if not character.player_can_edit(request.user):
        raise PermissionDenied("This Contractor has been deleted, or you're not allowed to edit it")
    character_image = get_object_or_404(CharacterImage, relevant_character=character_id, relevant_image=image_id)
    image = character_image.relevant_image
    if request.method == 'POST':
        form = DeleteImageForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                character.primary_image = image
                character.save()
    return HttpResponseRedirect(reverse('characters:characters_upload_image', args=(character_id,)))
