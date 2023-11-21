from collections import defaultdict, Counter
import json, datetime
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.forms import formset_factory
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from django.contrib import messages
from django.utils.safestring import mark_safe

from characters.models import Artifact, Character
from powers.models import Power, Power_Full, CRAFTING_ARTIFACT, CRAFTING_CONSUMABLE
from django.utils import timezone

from .models import NUM_FREE_CONSUMABLES_PER_DOWNTIME, CraftingEvent, CraftedArtifact, \
    NUM_FREE_CONSUMABLES_PER_REWARD, NUM_FREE_ARTIFACTS_PER_DOWNTIME, NUM_FREE_ARTIFACTS_PER_REWARD
from .forms import make_consumable_crafting_form, NewArtifactForm, make_artifact_gift_selector_form


@method_decorator(login_required(login_url='account_login'), name='dispatch')
class Craft(View):
    template_name = 'crafting/craft.html'
    character = None
    attendance = None
    crafting_events = None
    prev_crafted_consumables = None
    prev_crafted_free_consumables = None
    event_by_power_full = None
    free_crafts_by_power_full = None

    def dispatch(self, *args, **kwargs):
        if self.request.user.profile.get_confirmed_email() is None:
            messages.add_message(self.request, messages.WARNING,
                                 mark_safe(
                                     "<h4 class=\"text-center\" style=\"margin-bottom:5px;\">You must validate your email address to craft</h4>"))
            return HttpResponseRedirect(reverse('account_resend_confirmation'))
        self.character = get_object_or_404(Character, pk=self.kwargs["character_id"])
        if not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You do not have permission to craft for this character")
        self.attendance = self.character.get_current_downtime_attendance()
        if self.attendance:
            if not self.attendance.is_confirmed:
                return HttpResponseRedirect(reverse('games:games_confirm_attendance', args=(self.attendance.pk,)))
        self.crafting_events = self.__get_crafting_events()
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            self.character = Character.objects.select_for_update().get(id=self.character.pk)
            page_data, consumable_forms, new_artifact_formset, artifact_gift_selector_formset = \
                self.__get_page_data_and_forms(request.POST)
            consumable_forms = [x[0] for x in consumable_forms] # strip the powers out
            for form in consumable_forms:
                if not form.is_valid():
                    raise ValueError("Invalid consumable form")
            if new_artifact_formset:
                for form in new_artifact_formset:
                    if not form.is_valid():
                        raise ValueError("Invalid new artifact form")
            if artifact_gift_selector_formset:
                for form in artifact_gift_selector_formset:
                    if not form.is_valid():
                        raise ValueError("Invalid artifact gift form")
                self.__save_artifact_forms(new_artifact_formset, artifact_gift_selector_formset)
            self.__save_consumable_forms(consumable_forms)
            self.character.refresh_from_db()
            self.character.highlight_crafting = False
            self.character.save()
            arts = self.character.artifact_set.filter(cell__isnull=True, is_crafted_artifact=True, is_deleted=False).all()
            for art in arts:
                if art.power_full_set.count() == 0:
                    art.delete()

        return HttpResponseRedirect(reverse('characters:characters_view', args=(self.character.pk,)))

    def __get_context_data(self):
        page_data, consumable_forms, new_artifact_formset, artifact_gift_selector_formset = self.__get_page_data_and_forms()
        return {
            "consumable_forms": consumable_forms,
            "new_artifact_formset": new_artifact_formset,
            "artifact_gift_selector_formset": artifact_gift_selector_formset,
            "page_data": json.dumps(page_data),
            "character": self.character,
        }

    def __save_artifact_forms(self, new_artifact_formset, artifact_gift_selector_formset):
        artifact_by_id = self.__create_artifact_map(new_artifact_formset, artifact_gift_selector_formset)
        artifacts_by_power_id = {}
        for choice in self.artifact_power_full_choices:
            artifacts_by_power_id[choice["pk"]] = []
        for form in artifact_gift_selector_formset:
            power_fulls = form.cleaned_data["selected_gifts"]
            artifact_id = form.cleaned_data["artifact_id"]
            for power in power_fulls:
                if power.pk not in artifacts_by_power_id:
                    raise ValueError("Invalid power in artifact form")
                artifacts_by_power_id[power.pk].append(artifact_by_id[artifact_id])
        for power_id in artifacts_by_power_id:
            artifacts = artifacts_by_power_id[power_id]
            artifacts.extend(self.artifacts_out_of_possession_by_power[power_id])
            allowed_num_free = self.free_crafts_by_power_full[power_id]
            if power_id in self.event_by_power_full:
                self.event_by_power_full[power_id].set_crafted_artifacts(artifacts, allowed_num_free)
            else:
                power_full = get_object_or_404(Power_Full, pk=power_id)
                crafting_event = CraftingEvent.objects.create(
                    relevant_attendance=self.attendance,
                    relevant_character=self.character,
                    relevant_power=power_full.latest_rev,
                    relevant_power_full=power_full)
                crafting_event.set_crafted_artifacts(artifacts, allowed_num_free)

    def __create_artifact_map(self, new_artifact_formset, artifact_gift_selector_formset):
        artifact_by_id = {}
        new_artifacts = set()
        powers_by_art_id = {}
        for form in artifact_gift_selector_formset:
            art_id = form.cleaned_data["artifact_id"]
            powers_by_art_id[art_id] = form.cleaned_data["selected_gifts"]
            if art_id < 0:
                if art_id in new_artifacts:
                    raise ValueError("duplicate new artifacts by id")
                new_artifacts.add(art_id)
            else:
                if art_id in artifact_by_id:
                    raise ValueError("duplicate existing artifacts by id")
                art = get_object_or_404(Artifact, pk=art_id, character=self.character)
                artifact_by_id[art_id] = art
        for form in new_artifact_formset:
            art_id = form.cleaned_data["artifact_id"]
            if art_id not in new_artifacts:
                raise ValueError("new artifact not referenced in gift forms")
            if art_id not in powers_by_art_id or not powers_by_art_id[art_id]:
                continue
            art = Artifact.objects.create(
                character=self.character,
                crafting_character=self.character,
                name=form.cleaned_data["name"],
                description=form.cleaned_data["description"],
                is_crafted_artifact=True,
                creating_player=self.character.player)
            artifact_by_id[art_id] = art
        out_of_pos_by_id = {x.pk: x for x in self.artifacts_out_of_possession}
        artifact_by_id.update(out_of_pos_by_id)
        return artifact_by_id

    def __save_consumable_forms(self, consumable_forms):
        for form in consumable_forms:
            crafted_quant = form.cleaned_data["num_crafted"]
            power_id = form.cleaned_data["power_full_id"]
            power = get_object_or_404(Power_Full, pk=power_id)
            prev_quantity = self.prev_crafted_consumables[power_id]
            newly_crafted = crafted_quant - prev_quantity
            number_free = max(min(self.free_crafts_by_power_full[power.pk] - prev_quantity, newly_crafted), 0)
            if power_id in self.event_by_power_full:
                # update an existing event
                if newly_crafted < 0:
                    self.event_by_power_full[power_id].refund_crafted_consumables(
                        number_to_refund=-newly_crafted)
                if newly_crafted > 0:
                    self.event_by_power_full[power_id].craft_new_consumables(
                        number_newly_crafted=newly_crafted,
                        new_number_free=number_free,
                        power_full=power)
            else:
                # No existing event
                if newly_crafted < 0:
                    raise ValueError("wanted to refund consumables, but no consumables to refund.")
                if newly_crafted > 0:
                    crafting_event = CraftingEvent.objects.create(
                        relevant_attendance=self.attendance,
                        relevant_character=self.character,
                        relevant_power=power.latest_rev,
                        relevant_power_full=power)
                    crafting_event.craft_new_consumables(
                        number_newly_crafted=newly_crafted,
                        new_number_free=number_free,
                        power_full=power)

    def __get_page_data_and_forms(self, POST=None):
        self.prev_crafted_consumables = Counter()
        self.prev_crafted_free_consumables = Counter()
        self.event_by_power_full = {ev.relevant_power_full_id: ev for ev in self.crafting_events}
        self.free_crafts_by_power_full = Counter()
        self.artifact_power_full_choices = []
        self.artifacts_out_of_possession = []
        self.artifacts_out_of_possession_by_power = defaultdict(list)

        consumable_forms = []
        consumable_details_by_power = defaultdict(list)
        initial_consumable_counts = {}

        power_fulls = self.character.power_full_set.all()

        # free crafting from rewards
        latest_end_game = self.attendance.relevant_game.end_time if self.attendance else None
        if latest_end_game:
            free_crafting_rewards = self.character.rewards_spent_since_date(latest_end_game) \
                .filter(is_void=False, relevant_power__parent_power__crafting_type__in=[CRAFTING_CONSUMABLE, CRAFTING_ARTIFACT]).all()
        else:
            free_crafting_rewards = self.character.spent_rewards()\
                .filter(is_void=False, relevant_power__parent_power__crafting_type__in=[CRAFTING_CONSUMABLE, CRAFTING_ARTIFACT]).all()
        for reward in free_crafting_rewards:
            power = reward.relevant_power
            if power.parent_power.crafting_type == CRAFTING_CONSUMABLE:
                self.free_crafts_by_power_full[power.parent_power.pk] += NUM_FREE_CONSUMABLES_PER_REWARD
            if power.parent_power.crafting_type == CRAFTING_ARTIFACT:
                self.free_crafts_by_power_full[power.parent_power.pk] += NUM_FREE_ARTIFACTS_PER_REWARD

        refundable_power_fulls_by_artifact_id = defaultdict(list)
        for power in power_fulls:
            if power.crafting_type == CRAFTING_CONSUMABLE:
                self.free_crafts_by_power_full[power.pk] += NUM_FREE_CONSUMABLES_PER_DOWNTIME
                if power.pk in self.event_by_power_full:
                    crafted_artifacts = self.event_by_power_full[power.pk].craftedartifact_set.all()
                    for artifact_craft in crafted_artifacts:
                        self.prev_crafted_consumables[power.pk] += artifact_craft.quantity
                        self.prev_crafted_free_consumables[power.pk] += artifact_craft.quantity_free
                        consumable_details_by_power[power.pk].append({
                            "owner": artifact_craft.relevant_artifact.character.name,
                            "name": artifact_craft.relevant_artifact.name,
                            "quantity": artifact_craft.quantity,
                            "free_quantity": artifact_craft.quantity_free,
                        })
                initial_craft_quantity = max(self.prev_crafted_consumables[power.pk],
                                             self.free_crafts_by_power_full[power.pk])
                initial_consumable_counts[power.pk] = initial_craft_quantity
                consumable_form = make_consumable_crafting_form(power)(POST, prefix=power.pk, initial={
                    "power_full_id": power.pk,
                    "num_crafted": initial_craft_quantity,
                })
                consumable_forms.append([consumable_form, power])
            if power.crafting_type == CRAFTING_ARTIFACT:
                self.free_crafts_by_power_full[power.pk] += NUM_FREE_ARTIFACTS_PER_DOWNTIME
                self.artifact_power_full_choices.append({
                    "pk": power.pk,
                    "name": power.name,
                })
                if power.pk in self.event_by_power_full:
                    crafted_artifacts = self.event_by_power_full[power.pk].craftedartifact_set.all()
                    for artifact_craft in crafted_artifacts:
                        refundable_power_fulls_by_artifact_id[artifact_craft.relevant_artifact_id].append(power.pk)
                        self.prev_crafted_consumables[power.pk] += artifact_craft.quantity

        new_artifact_formset = None
        artifact_gift_selector_formset = None
        if self.artifact_power_full_choices:
            new_artifact_formset = formset_factory(NewArtifactForm, extra=0)(POST, prefix="new_artifact")
            artifact_gift_selector_formset = formset_factory(make_artifact_gift_selector_form(self.character), extra=0)(POST, prefix="gift_selector")

        existing_artifacts = []
        existing_artifact_ids = set()
        #TODO: work here for crafting effects onto other peoples artifacts.
        crafted_artifacts = self.character.artifact_set.filter(is_crafted_artifact=True, crafting_character=self.character, is_deleted=False).all()
        for artifact in crafted_artifacts:
            current_fulls = set(artifact.power_full_set.values_list('id', flat=True))
            refundable_fulls = refundable_power_fulls_by_artifact_id[artifact.pk]
            current_fulls.difference_update(refundable_fulls)
            existing_artifact_ids.add(artifact.pk)
            existing_artifacts.append({
                "name": artifact.name,
                "description": artifact.description,
                "id": artifact.pk,
                "nonrefundable_power_fulls": list(current_fulls),
                "refundable_power_fulls": refundable_fulls,
            })

        for event in self.crafting_events:
            if event.relevant_power_full.crafting_type == CRAFTING_ARTIFACT:
                artifacts = event.artifacts
                for artifact in artifacts.all():
                    if artifact.pk not in existing_artifact_ids:
                        self.artifacts_out_of_possession_by_power[event.relevant_power_full_id].append(artifact)
                        self.artifacts_out_of_possession.append(artifact)
                        existing_artifact_ids.add(artifact.pk)

        artifacts_out_of_pos =[]
        for art in self.artifacts_out_of_possession:
            artifacts_out_of_pos.append({
                "name": art.name,
                "art_url": reverse("characters:characters_artifact_view", args=(art.pk,)),
                "holder": art.character.name,
                "holder_url": reverse("characters:characters_view", args=(art.character.pk,)),
            })
        page_data = {
            "prev_crafted_consumables": self.prev_crafted_consumables,
            "initial_consumable_counts": initial_consumable_counts,
            "free_crafts_by_power_full": self.free_crafts_by_power_full,
            "consumable_details_by_power": dict(consumable_details_by_power),
            "power_by_pk": {p.pk: p.to_crafting_blob() for p in power_fulls},
            "artifact_power_choices": self.artifact_power_full_choices,
            "existing_artifacts": existing_artifacts,
            "artifacts_out_of_pos": artifacts_out_of_pos,
        }
        return page_data, consumable_forms, new_artifact_formset, artifact_gift_selector_formset

    def __get_crafting_events(self):
        if self.attendance:
            return CraftingEvent.objects.filter(relevant_attendance=self.attendance)\
                .prefetch_related("craftedartifact_set") \
                .prefetch_related("relevant_power_full")\
                .all()
        else:
            return CraftingEvent.objects.filter(relevant_character=self.character, relevant_attendance__isnull=True) \
                .prefetch_related("relevant_power_full")\
                .all()


