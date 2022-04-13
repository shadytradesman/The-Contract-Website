from collections import defaultdict, Counter
import json
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction

from characters.models import Artifact, Character
from powers.models import Power, Power_Full, CRAFTING_ARTIFACT, CRAFTING_CONSUMABLE

from .models import NUM_FREE_CONSUMABLES_PER_DOWNTIME, CraftingEvent, CraftedArtifact, \
    NUM_FREE_CONSUMABLES_PER_REWARD, NUM_FREE_ARTIFACTS_PER_DOWNTIME, NUM_FREE_ARTIFACTS_PER_REWARD
from .forms import make_consumable_crafting_form, make_artifact_crafting_form


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
            page_data, consumable_forms = self.__get_page_data_and_forms(request.POST)
            consumable_forms = [x[0] for x in consumable_forms] # strip the powers out
            for form in consumable_forms:
                if not form.is_valid():
                    raise ValueError("Invalid consumable form")
            self.__save_consumable_forms(consumable_forms)
        return HttpResponseRedirect(reverse('characters:characters_view', args=(self.character.pk,)))

    def __get_context_data(self):
        page_data, consumable_forms = self.__get_page_data_and_forms()
        return {
            "consumable_forms": consumable_forms,
            "page_data": json.dumps(page_data),
            "character": self.character,
        }

    def __save_consumable_forms(self, consumable_forms):
        for form in consumable_forms:
            crafted_quant = form.cleaned_data["num_crafted"]
            power_id = form.cleaned_data["power_full_id"]
            power = get_object_or_404(Power_Full, pk=power_id)
            prev_quantity = self.prev_crafted_consumables[power_id]
            newly_crafted = crafted_quant - prev_quantity
            number_free = max(min(self.free_crafts_by_power_full[power.pk] - prev_quantity, newly_crafted), 0)
            print("MAP: ")
            print(self.event_by_power_full)
            print(power_id)
            if power_id in self.event_by_power_full:
                # update an existing event
                if newly_crafted < 0:
                    self.event_by_power_full[power_id].refund_crafted_consumables(
                        number_to_refund=-newly_crafted,
                        exp_cost_per=power.get_gift_cost())
                if newly_crafted > 0:
                    self.event_by_power_full[power_id].craft_new_consumables(
                        number_newly_crafted=newly_crafted,
                        exp_cost_per=power.get_gift_cost(),
                        new_number_free=number_free,)
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
                        exp_cost_per=power.get_gift_cost(),
                        number_free=number_free)

    def __get_page_data_and_forms(self, POST=None):
        self.prev_crafted_consumables = Counter()
        self.prev_crafted_free_consumables = Counter()
        self.event_by_power_full = {ev.relevant_power_full_id: ev for ev in self.crafting_events}
        self.free_crafts_by_power_full = Counter()

        consumable_forms = []
        consumable_details_by_power = defaultdict(list)
        initial_consumable_counts = {}

        power_fulls = self.character.power_full_set.all()

        # free crafting from rewards
        latest_end_game = self.attendance.relevant_game.end_time
        free_crafting_rewards = self.character.rewards_spent_since_date(latest_end_game) \
            .filter(relevant_power__parent_power__crafting_type__in=[CRAFTING_CONSUMABLE, CRAFTING_ARTIFACT]).all()
        for reward in free_crafting_rewards:
            power = reward.relevant_power
            if power.parent_power.crafting_type == CRAFTING_CONSUMABLE:
                self.free_crafts_by_power_full[power.parent_power.pk] += NUM_FREE_CONSUMABLES_PER_REWARD
            if power.parent_power.crafting_type == CRAFTING_ARTIFACT:
                self.free_crafts_by_power_full[power.parent_power.pk] += NUM_FREE_ARTIFACTS_PER_REWARD

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
                consumable_form = make_consumable_crafting_form(power)(POST, initial={
                    "power_full_id": power.pk,
                    "num_crafted": initial_craft_quantity,
                })
                consumable_forms.append([consumable_form, power])
            if power.crafting_type == CRAFTING_ARTIFACT:
                self.free_crafts_by_power_full[power.pk] += NUM_FREE_ARTIFACTS_PER_DOWNTIME

        page_data = {
            "prev_crafted_consumables": self.prev_crafted_consumables,
            "initial_consumable_counts": initial_consumable_counts,
            "free_crafts_by_power_full": self.free_crafts_by_power_full,
            "consumable_details_by_power": dict(consumable_details_by_power),
            "power_by_pk": {p.pk: p.to_crafting_blob() for p in power_fulls},
        }
        return page_data, consumable_forms

    def __get_crafting_events(self):
        if self.attendance:
            return CraftingEvent.objects.filter(relevant_attendance=self.attendance)\
                .prefetch_related("craftedartifact_set") \
                .prefetch_related("relevant_power_full")\
                .all()
        else:
            return CraftingEvent.objects.filter(relevant_character=self.character, is_pre_imbue=True) \
                .prefetch_related("relevant_power_full")\
                .all()


