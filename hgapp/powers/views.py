import random
from django.http import HttpResponseRedirect, HttpResponse,JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.views import View
from django.views import generic
from django.db import transaction
from django.db.models import Prefetch
from .signals import gift_major_revision

from characters.models import Character, Artifact
from .models import Power,  Base_Power, Power_Full,  PremadeCategory,  SYS_PS2, PowerImage
from django.contrib.auth.decorators import login_required
from .forms import DeletePowerForm, DeleteImageForm
from .ps2Utilities import get_edit_context, save_gift
from .templatetags.power_tags import power_badge
from images.forms import ImageUploadForm
from images.models import PrivateUserImage

class EditPower(View):
    template_name = 'powers/ps2_create_pages/create_ps2.html'
    existing_power = None
    power_to_edit = None
    character = None
    artifact = None

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
            new_power_full = save_gift(request, power_full=self.power_to_edit, character=self.character, existing_artifact=self.artifact)
        return HttpResponseRedirect(reverse('powers:powers_view_power', args=(new_power_full.id,)))

    def __check_permissions(self):
        pass # Ps2 is released!

    def __get_context_data(self):
        return get_edit_context(existing_power_full=self.existing_power,
                                is_edit=self.power_to_edit,
                                existing_char=self.character,
                                user=self.request.user,
                                existing_artifact=self.artifact)


class CreatePower(EditPower):
    def dispatch(self, *args, **kwargs):
        if 'character_id' in self.kwargs:
            self.character = get_object_or_404(Character, id=self.kwargs['character_id'])
        if 'artifact_id' in self.kwargs:
            self.artifact = get_object_or_404(Artifact, id=self.kwargs['artifact_id'])
            self.character = self.artifact.crafting_character
        if 'power_full_id' in self.kwargs:
            self.existing_power = get_object_or_404(Power_Full, id=self.kwargs['power_full_id'])
            if not self.existing_power.player_can_view(self.request.user):
                raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
        self.__check_permissions()
        return super().dispatch(*args, **kwargs)

    def __check_permissions(self):
        if self.character and not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You can't give Gifts to a Character you can't edit.")


class EditExistingPower(EditPower):

    def dispatch(self, *args, **kwargs):
        self.existing_power = get_object_or_404(Power_Full, id=self.kwargs['power_full_id'])
        self.power_to_edit = self.existing_power
        if self.existing_power.character:
            self.character = self.existing_power.character
        self.__check_permissions()
        return super().dispatch(*args, **kwargs)

    def __check_permissions(self):
        if not self.existing_power.player_can_edit(self.request.user):
            raise PermissionDenied("This Power has been deleted, or you're not allowed to view it")
        if self.character and not self.character.player_can_edit(self.request.user):
            raise PermissionDenied("You can't give Gifts to a Character you can't edit.")

def powers_and_examples(request):
    base_powers_list = Base_Power.objects.order_by('name').all()
    only_examples = Power_Full.objects.filter(tags__in=["example"])
    only_examples = [x for x in only_examples if x.tags.count() == 1]
    context = {
        'base_powers_list': base_powers_list,
        'only_examples': only_examples,
    }
    return render(request, 'powers/powers_and_examples.html', context)


@login_required
def my_gifts(request):
    unassigned_powers = request.user.power_full_set.filter(is_deleted=False, character__isnull=True).select_related('latest_rev').order_by('name').all()
    context = {
        'unassigned_powers': unassigned_powers,
    }
    return render(request, 'powers/my_gifts.html', context)


def powers_and_effects(request):
    base_powers_list = Base_Power.objects.filter(is_public=True).order_by('name').all()
    context = {
        'base_powers_list': base_powers_list,
    }
    return render(request, 'powers/powers_and_effects.html', context)


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
                gift_major_revision.send(sender=Power.__class__, old_power=None, new_power=power_full.latest_rev,
                                         power_full=power_full)
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
        context['can_edit'] = self.power.player_can_edit(self.request.user)
        context['images'] = self.power.images.all()
        return context


def power_full_view(request, power_full_id):
    power_full = get_object_or_404(Power_Full, id=power_full_id)
    if not power_full.player_can_view(request.user):
        raise PermissionDenied("This Power has been deleted or you're not allowed to view it")
    most_recent_power = power_full.latest_revision()
    return ViewPower.as_view()(request, power_id=most_recent_power.id)


def ajax_example_view(request, effect_id):
    print(effect_id)
    power_full = Power_Full.objects.filter(dice_system=SYS_PS2, tags__in=["example"], latest_rev__base=effect_id).first()
    if not power_full.player_can_view(request.user):
        raise PermissionDenied("This Power has been deleted or you're not allowed to view it")
    preview_badge = get_stock_gift_display(request, None, power_full)
    edit_blob = power_full.latest_revision().to_edit_blob()
    return JsonResponse({"preview": preview_badge, "edit_blob": edit_blob}, status=200)


def stock(request, character_id=None):
    if character_id:
        character = get_object_or_404(Character, id=character_id)
    else:
        character = None
    use_cache = character_id is None
    generic_categories = PremadeCategory.objects.order_by("name").all()
    generic_powers_by_category = {}
    total_gift_count = 0
    for cat in generic_categories:
        artifacts_query = Artifact.objects.filter(is_signature=True)
        all_powers = Power_Full.objects \
            .filter(tags__slug__in=cat.tags.all(), is_deleted=False) \
            .prefetch_related(Prefetch("artifacts", queryset=artifacts_query)) \
            .order_by("-stock_order", "name") \
            .all()
        powers = []
        consumables = []
        artifact_crafting = []
        artifacts = set()
        for power in all_powers:
            total_gift_count += 1
            if power.is_signature():
                item = power.artifacts.filter(is_signature=True).first()
                if item:
                    artifacts.add(item)
            elif power.is_consumable_crafting():
                consumables.append(get_stock_gift_display(request, character, power, use_cache))
            elif power.is_artifact_crafting():
                artifact_crafting.append(get_stock_gift_display(request, character, power, use_cache))
            elif power.is_power():
                powers.append(get_stock_gift_display(request, character, power, use_cache))
        generic_powers_by_category[cat] = (powers, consumables, artifact_crafting, artifacts)
    context = {
        "generic_powers_by_category": generic_powers_by_category,
        'main_modal_art_url': static('overrides/art/mime.jpeg'),
        "rewarding_character": character,
        "show_tutorial": (not request.user) or (not request.user.is_authenticated) or (
            not request.user.power_full_set.exists()),
        "total_gift_count": total_gift_count,
        'powers_modal_art_url': static('overrides/art/grace.png'),
        'sig_item_modal_art_url': static('overrides/art/lady_lake_sm.jpg'),
        'art_craft_modal_art_url': static('overrides/art/front-music.jpg'),
        'consumable_craft_modal_art_url': static('overrides/art/sushi.jpg'),
        'mod_power': get_object_or_404(Base_Power, slug='power'),
        'mod_sig_item': get_object_or_404(Base_Power, slug='signature-item-mod'),
        'mod_consumable': get_object_or_404(Base_Power, slug='craftable-consumable'),
        'mod_artifacts': get_object_or_404(Base_Power, slug='craftable-artifact'),
    }
    return render(request, 'powers/stock_powers.html', context)


def get_stock_gift_display(request, rewarding_character, power, use_cache=True):
    if use_cache:
        cache_key = "{}{}".format("stockGift", power.pk)
        sentinel = object()
        cache_contents = cache.get(cache_key, sentinel)
        if cache_contents is sentinel:
            cache_contents = render_to_string(
                'powers/power_badge_snippet.html',
                power_badge({"request": request}, power, False, None, False, rewarding_character, True),
                request)
            cache.set(cache_key, cache_contents, 8000)
        return cache_contents
    else:
        return render_to_string('powers/power_badge_snippet.html',
                                power_badge({"request":request}, power, False, None, False, rewarding_character, True),
                                request)



def toggle_active(request, power_id, is_currently_active, art_id=None):
    power = get_object_or_404(Power, id=power_id)
    if not power.player_can_edit(request.user):
        raise PermissionDenied("This Power has been deleted, or you're not allowed to edit it")
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


@login_required
def upload_image(request, power_id):
    power = get_object_or_404(Power, id=power_id)
    if not request.user.is_authenticated and request.user.profile.early_access_user:
        raise PermissionDenied("Early Access only")
    if not power.player_can_edit(request.user):
        raise PermissionDenied("This Power has been deleted, or you're not allowed to edit it")
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                new_image = PrivateUserImage.objects.create(
                    image=request.FILES['file'],
                    uploader=request.user,
                )
                power.images.add(new_image)
        else:
            raise ValueError("Invalid image upload form")
    upload_form = ImageUploadForm()
    images = power.images.all()
    context = {
        "power": power,
        "upload_form": upload_form,
        "delete_form": DeleteImageForm(),
        "images": images,
    }
    return render(request, 'powers/manage_images.html', context)


@login_required
def delete_image(request, power_id, image_id):
    power = get_object_or_404(Power, id=power_id)
    if not request.user.is_authenticated and request.user.profile.early_access_user:
        raise PermissionDenied("Early Access only")
    if not power.player_can_edit(request.user):
        raise PermissionDenied("This Power has been deleted, or you're not allowed to edit it")
    power_image = get_object_or_404(PowerImage, relevant_power=power_id, relevant_image=image_id)
    image = power_image.relevant_image
    if request.method == 'POST':
        form = DeleteImageForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                if form.cleaned_data["from_all_revisions"]:
                    if hasattr(power, "parent_power") and power.parent_power is not None:
                        power_revisions = Power.objects.filter(parent_power=power.parent_power_id).all()
                        for power_rev in power_revisions:
                            power_rev.images.remove(image)
                    else:
                        power.images.remove(image)
                else:
                    power.images.remove(image)
    return HttpResponseRedirect(reverse('powers:powers_upload_image', args=(power_id,)))
