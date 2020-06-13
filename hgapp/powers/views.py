from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views import generic
from django.views.generic import ListView
from guardian.shortcuts import assign_perm

from characters.models import Character
from .createPowerFormUtilities import get_create_power_context_from_base, \
    get_create_power_context_from_power, get_edit_power_context_from_power, create_new_power_and_parent, \
    create_power_for_new_edit, refund_or_assign_rewards
from .models import Power, Base_Power_Category, Base_Power, Base_Power_System, DICE_SYSTEM, Power_Full


def index(request):
    latest_power_list = Power.objects.filter(private=False).order_by('-id')[:40]
    context = {
        'latest_power_list': latest_power_list,
    }
    return render(request, 'powers/index.html', context)

def tutorial(request):
    return render(request, 'powers/tutorial.html')

def create(request, character_id=None):
    category_list = Base_Power_Category.objects.order_by('name')
    character=None
    if character_id:
        character = get_object_or_404(Character, pk=character_id)
    context = {
        'category_list': category_list,
        'character': character,
    }
    return render(request, 'powers/choosecat.html', context)

def powers_and_examples(request):
    base_powers_list = Base_Power.objects.order_by('name').all()
    context = {
        'base_powers_list': base_powers_list,
    }
    return render(request, 'powers/powers_and_examples.html', context)

def create_category(request, category_slug, character_id=None):
    powers_list = Base_Power.objects.filter(category = category_slug, is_public = True)
    category = get_object_or_404(Base_Power_Category, pk=category_slug)
    character = None
    if character_id:
        character = get_object_or_404(Character, pk=character_id)
    context = {
        'powers_list': powers_list,
        'category': category,
        'character': character,
    }
    return render(request, 'powers/choosebasecat.html', context)

def create_all(request, character_id=None):
    powers_list = Base_Power.objects.filter(is_public = True).order_by('name')
    character = None
    if character_id:
        character = get_object_or_404(Character, pk=character_id)
    context = {
        'powers_list': powers_list,
        'character': character,
    }
    return render(request, 'powers/choosebaseall.html', context)

def create_power(request, base_power_slug, character_id=None):
    base_power = get_object_or_404(Base_Power, pk=base_power_slug)
    character = None
    if character_id:
        character = get_object_or_404(Character, pk=character_id)
        if not character.player_can_edit(request.user):
            return HttpResponseForbidden()
    if request.method == 'POST':
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
    base_power = get_object_or_404(Base_Power, pk=extant_power.base.slug)
    if request.method == 'POST':
        new_power = create_new_power_and_parent(base_power, request)
        if (new_power):
            return HttpResponseRedirect(reverse('powers:powers_view_power', args=(new_power.id,)))
        else:
            print("ERROR CREATING POWER")
    else:
        # Build a power form.
        if not extant_power.player_can_view(request.user):
            return HttpResponseForbidden()
        context = get_create_power_context_from_power(extant_power)
        return render(request, 'powers/create_power_pages/createpower.html', context)

def edit_power(request, power_id):
    power_full = get_object_or_404(Power_Full, pk=power_id)
    if not power_full.player_can_edit(request.user):
        return HttpResponseForbidden()
    extant_power = power_full.power_set.order_by('-pub_date').all()[0]
    base_power = get_object_or_404(Base_Power, pk=extant_power.base.slug)
    if request.method == 'POST':
        new_power = create_power_for_new_edit(base_power, request, power_full)
        if (new_power):
            refund_or_assign_rewards(new_power, extant_power)
            return HttpResponseRedirect(reverse('powers:powers_view_power', args=(new_power.id,)))
        else:
            print("ERROR CREATING POWER")
    else:
        # Build a power form.
        context = get_edit_power_context_from_power(extant_power)
        return render(request, 'powers/create_power_pages/edit_power.html', context)


def power_view(request, power_id):
    power = get_object_or_404(Power, id=power_id)
    if not power.player_can_view(request.user):
        return HttpResponseForbidden()
    if power.parent_power:
        power_full = Power_Full.objects.filter(id=power.parent_power.id).all().first()
        power_list = power_full.power_set.order_by('-pub_date').all()
        if power_list[0] == power and "history" not in request.path:
            return HttpResponseRedirect(reverse('powers:powers_view_power_full', args=(power_full.id,)))
    else:
        power_full = None
        power_list = None
    context = {}
    context['power'] = power
    context['power_list'] = power_list
    context['power_full'] = power_full
    return render(request, 'powers/viewpower.html', context)


def power_full_view(request, power_full_id):
    power_full = get_object_or_404(Power_Full, id=power_full_id)
    if not power_full.player_can_view(request.user):
        return HttpResponseForbidden()
    most_recent_power = power_full.power_set.order_by('-pub_date').all()[0]
    return power_view(request, power_id=most_recent_power.id)


class BrowsePowersView(ListView):
    model = Power
    template_name = 'powers/browse_powers.html'
    queryset = Power.objects.filter(private=False).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super(BrowsePowersView, self).get_context_data(**kwargs)
        context['now'] = timezone.now()
        return context


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