from collections import defaultdict
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms import formset_factory
from django.views import View
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction

from characters.models import Artifact, Character
from powers.models import Power, Power_Full, CRAFTING_ARTIFACT, CRAFTING_CONSUMABLE

from .models import NUM_FREE_CONSUMABLES_PER_DOWNTIME, CraftingEvent, CraftedArtifact
from .forms import ConsumableCraftingForm, ArtifactCraftingForm


@method_decorator(login_required(login_url='account_login'), name='dispatch')
class Craft(View):
    template_name = 'crafting/craft.html'
    character = None
    attendance = None

    def dispatch(self, *args, **kwargs):
        self.character = get_object_or_404(Character, pk=self.kwargs["character_id"])
        if not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You do not have permission to craft for this character")
        self.attendance = self.character.get_current_downtime_attendance()
        if self.attendance:
            if not self.attendance.is_confirmed:
                return HttpResponseRedirect(reverse('games:games_confirm_attendance', args=(self.attendance.pk,)))
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            pass
            # = save_gift(request, power_full=self.power_to_edit, character=self.character)
        return HttpResponseRedirect(reverse('characters:view_character', args=(self.character.pk,)))

    def __get_context_data(self, POST=None):
        crafting_events = self.__get_crafting_events()
        event_by_power_full = {ev.relevant_power.pk: ev for ev in crafting_events}
        power_fulls = self.character.power_full_set.all()

        artifact_formset_initial = []
        consumable_forms = []
        consumable_details_by_power = defaultdict(list)

        for power in power_fulls:
            if power.crafting_type == CRAFTING_ARTIFACT:
                if power.pk in event_by_power_full:
                    artifact_formset_initial.append({
                        "power_full_id": power.pk,
                        "artifact_id": event_by_power_full[power.pk].pk,
                        "refund": False,
                        "upgrade": True,
                    })
            if power.crafting_type == CRAFTING_CONSUMABLE:
                if power.pk in event_by_power_full:
                    crafted_artifacts = event_by_power_full[power.pk].craftedartifact_set()
                    quantity_made = 0
                    for artifact in crafted_artifacts:
                        quantity_made = quantity_made + artifact.quantity
                        consumable_details_by_power[power.pk].append({
                            "owner": artifact.relevant_artifact.character.name,
                            "name": artifact.relevant_artifact.name,
                            "quantity": artifact.quantity,
                            "free_quantity": artifact.quantity_free,
                        })
                    consumable_forms.append(ConsumableCraftingForm(POST, initial={
                        "power_full_id": power.pk,
                        "num_crafted": quantity_made,
                    }))
                else:
                    consumable_forms.append(ConsumableCraftingForm(POST, initial={
                        "power_full_id": power.pk,
                        "num_crafted": NUM_FREE_CONSUMABLES_PER_DOWNTIME,
                    }))

        ArtifactCraftingFormset = formset_factory(ArtifactCraftingForm, extra=0)
        artifact_formset = ArtifactCraftingFormset(POST, initial=artifact_formset_initial)

        # artifacts, details
        return {
            "artifact_formset": artifact_formset,
            "consumable_forms": consumable_forms,
            "consumable_details_by_power": dict(consumable_details_by_power),
            "character": self.character,
        }

    def __get_crafting_events(self):
        if self.attendance:
            return CraftingEvent.objects.filter(relevant_attendance=self.attendance).all()
        else:
            return CraftingEvent.objects.filter(relevant_character=self.character, is_pre_imbue=True).all()


