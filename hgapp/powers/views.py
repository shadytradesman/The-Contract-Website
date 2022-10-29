from collections import defaultdict
import random
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static
from django.views import View
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.forms import formset_factory
from django.db import transaction
from django.db.models import Prefetch

from characters.models import Character, Artifact
from .createPowerFormUtilities import get_create_power_context_from_base, \
    get_create_power_context_from_power, get_edit_power_context_from_power, create_new_power_and_parent, \
    create_power_for_new_edit, refund_or_assign_rewards
from .models import Power, Base_Power_Category, Base_Power, Base_Power_System, DICE_SYSTEM, Power_Full, PowerTag, \
    PremadeCategory, PowerTutorial, SYS_PS2, EFFECT, VECTOR, MODALITY
from .forms import DeletePowerForm
from .ps2Utilities import get_edit_context, save_gift

class EditPower(View):
    template_name = 'powers/ps2_create_pages/create_ps2.html'
    existing_power = None
    power_to_edit = None
    character = None

    def dispatch(self, *args, **kwargs):
        redirect = self.__check_permissions()
        if redirect:
            return redirect
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.__get_context_data())

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            if self.character:
                self.character = Character.objects.select_for_update().get(pk=self.character.id)
            if self.power_to_edit:
                self.power_to_edit = Power_Full.objects.select_for_update().get(pk=self.power_to_edit.id)
            new_power_full = save_gift(request, power_full=self.power_to_edit, character=self.character)
        return HttpResponseRedirect(reverse('powers:powers_view_power', args=(new_power_full.id,)))

    def __check_permissions(self):
        pass # Ps2 is released!

    def __get_context_data(self):
        return get_edit_context(existing_power_full=self.existing_power,
                                is_edit=self.power_to_edit,
                                existing_char=self.character,
                                user=self.request.user)


class CreatePower(EditPower):
    def dispatch(self, *args, **kwargs):
        if 'character_id' in self.kwargs:
            self.character = get_object_or_404(Character, id=self.kwargs['character_id'])
        if 'power_full_id' in self.kwargs:
            self.existing_power = get_object_or_404(Power_Full, id=self.kwargs['power_full_id'])
            if not self.existing_power.player_can_view(self.request.user):
                raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
        return super().dispatch(*args, **kwargs)

    def __check_permissions(self):
        if self.character and not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You can't give Gifts to a Character you can't edit.")
        return super().__check_permissions()


class EditExistingPower(EditPower):

    def dispatch(self, *args, **kwargs):
        self.existing_power = get_object_or_404(Power_Full, id=self.kwargs['power_full_id'])
        self.power_to_edit = self.existing_power
        if self.existing_power.character:
            self.character = self.existing_power.character
        return super().dispatch(*args, **kwargs)

    def __check_permissions(self):
        if not self.existing_power.player_can_edit(self.request.user):
            raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
        return super().__check_permissions()


def create(request, character_id=None):
    if character_id:
        return HttpResponseRedirect(reverse('powers:powers_create_ps2_for_char', args=(character_id,)))
    else:
        return HttpResponseRedirect(reverse('powers:powers_create_ps2', ))
    category_list = Base_Power_Category.objects\
        .prefetch_related(Prefetch('base_power_set',queryset=Base_Power.objects.order_by('name')))\
        .order_by('name')
    category_list = [x for x in category_list if x.base_power_set.filter(is_public=True).count() > 0]
    character=None
    show_tutorial = (not request.user.is_authenticated) or (not request.user.power_full_set.exists())
    tutorial = get_object_or_404(PowerTutorial)
    context = {
        'category_list': category_list,
        'character': character,
        'show_tutorial': show_tutorial,
        'modal_header': tutorial.modal_base_header,
        'modal_text': tutorial.modal_base,
        'modal_art': 'overrides/art/lady_lake_sm.jpg',
    }
    return render(request, 'powers/choosecat.html', context)

def powers_and_examples(request):
    base_powers_list = Base_Power.objects.order_by('name').all()
    context = {
        'base_powers_list': base_powers_list,
    }
    return render(request, 'powers/powers_and_examples.html', context)

def powers_and_effects(request):
    base_powers_list = Base_Power.objects.filter(is_public=True).order_by('name').all()
    context = {
        'base_powers_list': base_powers_list,
    }
    return render(request, 'powers/powers_and_effects.html', context)

def create_category(request, category_slug, character_id=None):
    return HttpResponseRedirect(reverse('powers:powers_create_ps2', ))
    powers_list = Base_Power.objects.filter(category=category_slug, is_public=True)
    category = get_object_or_404(Base_Power_Category, pk=category_slug)
    character = None
    if character_id:
        character = get_object_or_404(Character, pk=character_id)
    tutorial = get_object_or_404(PowerTutorial)
    context = {
        'powers_list': powers_list,
        'category': category,
        'character': character,
        'modal_header': tutorial.modal_base_header,
        'modal_text': tutorial.modal_base,
        'modal_art': 'overrides/art/lady_lake_sm.jpg',
    }
    return render(request, 'powers/choosebasecat.html', context)

def create_all(request, character_id=None):
    return HttpResponseRedirect(reverse('powers:powers_create_ps2', ))
    powers_list = Base_Power.objects.filter(is_public=True).order_by('name')
    character = None
    if character_id:
        character = get_object_or_404(Character, pk=character_id)
    tutorial = get_object_or_404(PowerTutorial)
    context = {
        'powers_list': powers_list,
        'character': character,
        'modal_header': tutorial.modal_base_header,
        'modal_text': tutorial.modal_base,
        'modal_art': 'overrides/art/lady_lake_sm.jpg',
    }
    return render(request, 'powers/choosebaseall.html', context)

def create_power(request, base_power_slug, character_id=None):
    if character_id:
        return HttpResponseRedirect(reverse('powers:powers_create_ps2_for_char', args=(character_id,)))
    else:
        return HttpResponseRedirect(reverse('powers:powers_create_ps2', ))
    base_power = get_object_or_404(Base_Power, pk=base_power_slug)
    if base_power.base_type in [VECTOR, MODALITY] or base_power.base_power_system_set.exclude(dice_system=SYS_PS2).count() == 0:
        raise PermissionDenied("SHH! Pay no attention to the man behind the curtain")
    character = None
    if character_id:
        character = get_object_or_404(Character, pk=character_id)
        if not character.player_can_edit(request.user):
            raise PermissionDenied("You can't give Gifts to a Character you can't edit.")
    if request.method == 'POST':
        with transaction.atomic():
            power = create_new_power_and_parent(base_power, request, character)
            if (power):
                if character:
                    refund_or_assign_rewards(power)
                return HttpResponseRedirect(reverse('powers:powers_view_power', args=(power.id,)))
            else:
                print("ERROR CREATING POWER")
    else:
        # Build a power form.
        context = get_create_power_context_from_base(base_power, character)
        return render(request, 'powers/create_power_pages/createpower.html', context)


def create_power_from_existing(request, power_id):
    extant_power = get_object_or_404(Power, pk=power_id)
    return HttpResponseRedirect(reverse('powers:powers_create_from_existing_ps2', args=(extant_power.parent_power_id,)))
    base_power = get_object_or_404(Base_Power, pk=extant_power.base.slug)
    if request.method == 'POST':
        with transaction.atomic():
            new_power = create_new_power_and_parent(base_power, request)
        if (new_power):
            return HttpResponseRedirect(reverse('powers:powers_view_power', args=(new_power.id,)))
        else:
            print("ERROR CREATING POWER")
    else:
        # Build a power form.
        if not extant_power.player_can_view(request.user):
            raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
        context = get_create_power_context_from_power(extant_power, False)
        return render(request, 'powers/create_power_pages/createpower.html', context)

def edit_power(request, power_id):
    return HttpResponseRedirect(reverse('powers:powers_edit_ps2', args=(power_id,)))
    power_full = get_object_or_404(Power_Full, pk=power_id)
    if not power_full.player_can_edit(request.user):
        raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
    extant_power = power_full.power_set.order_by('-pub_date').all()[0]
    base_power = get_object_or_404(Base_Power, pk=extant_power.base.slug)
    if request.method == 'POST':
        with transaction.atomic():
            new_power = create_power_for_new_edit(base_power, request, power_full)
            if new_power:
                refund_or_assign_rewards(new_power, extant_power)
                return HttpResponseRedirect(reverse('powers:powers_view_power', args=(new_power.id,)))
            else:
                print("ERROR CREATING POWER")
    else:
        # Build a power form.
        context = get_edit_power_context_from_power(extant_power)
        return render(request, 'powers/create_power_pages/edit_power.html', context)

def delete_power(request, power_id):
    power_full = get_object_or_404(Power_Full, pk=power_id)
    if not power_full.player_can_edit(request.user):
        raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
    if power_full.owner != request.user:
        raise PermissionDenied("You must own a Power to delete it")
    if request.method == 'POST':
        char = power_full.character
        if DeletePowerForm(request.POST).is_valid():
            with transaction.atomic():
                power_full.delete()
        else:
            raise ValueError("could not delete power")
        if char:
            return HttpResponseRedirect(reverse('characters:characters_view', args=(char.id,)))
        return HttpResponseRedirect(reverse('home'))
    else:
        context = {"form": DeletePowerForm(),
                   "power": power_full}
        return render(request, 'powers/delete_power.html', context)


class ViewPower(View):
    template_name = None
    power = None

    def dispatch(self, *args, **kwargs):
        self.power = get_object_or_404(Power, id=kwargs["power_id"])
        redirect = self.__check_permissions()
        if redirect:
            return redirect
        if self.power.parent_power:
            power_full = Power_Full.objects.get(id=self.power.parent_power.id)
            if power_full.latest_revision() == self.power and "revision" in self.request.path:
                return HttpResponseRedirect(reverse('powers:powers_view_power_full', args=(power_full.id,)))
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        if self.power.dice_system == SYS_PS2:
            self.template_name = 'powers/ps2_view_pages/view_power.html'
        else:
            self.template_name = 'powers/viewpower.html'
        return render(request, self.template_name, self.__get_context_data())

    def __check_permissions(self):
        if not self.power.player_can_view(self.request.user):
            raise PermissionDenied("This Power has been deleted or you're not allowed to view it")

    def __get_context_data(self):
        attribute_val_by_id = None
        ability_val_by_id = None
        if self.power.parent_power:
            power_full = Power_Full.objects.get(id=self.power.parent_power.id)
            power_list = power_full.power_set.order_by('-pub_date').all()
            if power_full.character:
                attribute_val_by_id = power_full.character.get_attribute_values_by_id()
                ability_val_by_id = power_full.character.get_ability_values_by_id()
        else:
            power_full = None
            power_list = None
        character = power_full.character if power_full.character else None
        show_status_warning = False
        if character:
            show_status_warning = not self.power.passes_status_check(character.status)

        related_gifts = []
        stock_gifts = []
        related_component = None
        sig_artifacts = None
        if self.power.dice_system == SYS_PS2:
            if power_full:
                sig_artifacts = power_full.artifacts.filter(is_signature=True).all()
            related_gift_query = Power_Full.objects.filter(dice_system=SYS_PS2, character__isnull=False, character__private=False)
            stock_gift_query = Power_Full.objects.filter(dice_system=SYS_PS2, tags__in=["example"])
            component = random.choice(["Effect", "Vector", "Modality"])
            if component == "Effect":
                related_gift_query = related_gift_query.filter(base=self.power.base_id)
                stock_gift_query = stock_gift_query.filter(base=self.power.base_id)
                related_component = self.power.base
            if component == "Vector":
                related_gift_query = related_gift_query.filter(latest_rev__vector=self.power.vector_id)
                stock_gift_query = stock_gift_query.filter(latest_rev__vector=self.power.vector_id)
                related_component = self.power.vector
            if component == "Modality":
                related_gift_query = related_gift_query.filter(latest_rev__modality=self.power.modality_id)
                stock_gift_query = stock_gift_query.filter(latest_rev__modality=self.power.modality_id)
                related_component = self.power.modality
            related_gifts = related_gift_query.order_by('?')[:5]
            stock_gifts = stock_gift_query.order_by('?')[:5]
        context = {}
        context['related_gifts'] = related_gifts
        context['stock_gifts'] = stock_gifts
        context['related_component'] = related_component
        context['show_status_warning'] = show_status_warning
        context['power'] = self.power
        context['power_list'] = power_list
        context['power_full'] = power_full
        context['ability_value_by_id'] = ability_val_by_id
        context['attribute_value_by_id'] = attribute_val_by_id
        context['sig_artifacts'] = sig_artifacts
        return context


def power_full_view(request, power_full_id):
    power_full = get_object_or_404(Power_Full, id=power_full_id)
    if not power_full.player_can_view(request.user):
        raise PermissionDenied("This Power has been deleted or you're not allowed to view it")
    most_recent_power = power_full.latest_revision()
    return ViewPower.as_view()(request, power_id=most_recent_power.id)


def stock(request, character_id=None):
    if character_id:
        character = get_object_or_404(Character, id=character_id)
    else:
        character = None
    generic_categories = PremadeCategory.objects.order_by("name").all()
    generic_powers_by_category = {}
    total_gift_count = Power_Full.objects.filter(tags__isnull=False, is_deleted=False).count()
    for cat in generic_categories:
        non_artifact_powers = Power_Full.objects\
            .filter(tags__slug__in=cat.tags.all(), artifacts__isnull=True, is_deleted=False) \
            .select_related("latest_rev")\
            .order_by("-stock_order", "name")\
            .all()
        artifact_powers = Power_Full.objects.filter(tags__slug__in=cat.tags.all(), artifacts__isnull=False, is_deleted=False) \
            .prefetch_related(Prefetch("artifacts", queryset=Artifact.objects.filter(is_signature=True))).all()
        artifacts = set()
        for power in artifact_powers:
            artifacts.update(list(power.artifacts.filter(is_signature=True).all()))
        generic_powers_by_category[cat] = (non_artifact_powers, artifacts)
    context = {
        "generic_powers_by_category": generic_powers_by_category,
        'main_modal_art_url': static('overrides/art/mime.jpeg'),
        "rewarding_character": character,
        "show_tutorial": (not request.user) or (not request.user.is_authenticated) or (not request.user.power_full_set.exists()),
        "total_gift_count": total_gift_count,
    }
    return render(request, 'powers/stock_powers.html', context)

class BasePowerDetailView(generic.DetailView):
    model = Base_Power
    template_name = 'powers/view_base_power.html'

    def get_queryset(self):
        self.base_power = get_object_or_404(Base_Power, slug=self.kwargs['pk'])
        return Base_Power.objects

    def get_context_data(self, **kwargs):
        context = super(BasePowerDetailView, self).get_context_data(**kwargs)
        context['system_text'] = Base_Power_System.objects.filter(dice_system=DICE_SYSTEM[1][0]).get(base_power=self.base_power)
        context['base_power'] = self.base_power
        return context


def toggle_active(request, power_id, is_currently_active, art_id=None):
    power = get_object_or_404(Power, id=power_id)
    if not power.player_can_edit(request.user):
        raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
    character = power.parent_power.character if power.parent_power.character else None
    if art_id:
        artifact = get_object_or_404(Artifact, id=art_id)
        if artifact.character:
            character = artifact.character
            if not artifact.character.player_can_view(request.user):
                raise PermissionDenied("This Artifact has been deleted, or you're not allowed to view it")
    else:
        artifact = None
    if request.method == 'POST':
        if DeletePowerForm(request.POST).is_valid():
            with transaction.atomic():
                power.set_is_active(is_currently_active == "False", artifact)
                character.reset_attribute_bonuses()
    else:
        raise ValueError("must be POST")
    char = artifact.character if artifact else power.parent_power.character
    return HttpResponseRedirect(reverse('characters:characters_view', args=(char.id,)))
