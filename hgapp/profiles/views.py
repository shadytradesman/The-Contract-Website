from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.db import transaction
from django.utils import timezone


from profiles.forms import EditProfileForm, AcceptTermsForm
from profiles.models import Profile
from info.terms import EULA, TERMS, PRIVACY

class ProfileView(generic.DetailView):
    template_name = 'profiles/view_profile.html'

    def get_queryset(self):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        if self.profile.user == self.request.user:
            self.powers = self.profile.user.power_full_set.filter(is_deleted=False).order_by('-pub_date').all()
            self.characters = self.profile.user.character_set.filter(is_deleted=False).order_by('-edit_date').all()
        else:
            self.powers = self.profile.user.power_full_set.filter(private=False, is_deleted=False).order_by('-pub_date').all()
            self.characters = self.profile.user.character_set.filter(private=False).order_by('-edit_date').all()
        return Profile.objects

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        context['profile'] = self.profile
        context['powers'] = self.powers
        context['characters'] = self.characters
        return context

def my_profile_view(request):
    profile = get_object_or_404(Profile, pk=request.user.pk)
    powers = request.user.power_full_set.filter(is_deleted=False).order_by('-pub_date').all()
    characters = request.user.character_set.filter(is_deleted=False).order_by('-edit_date').all()
    context = {
        'profile': profile,
        'powers': powers,
        'characters': characters,
    }
    return render(request, 'profiles/view_profile.html', context)

def profile_edit(request):
    profile = get_object_or_404(Profile, pk=request.user.pk)
    if request.method == 'POST':
        form = EditProfileForm(request.POST)
        if form.is_valid():
            profile.about = form.cleaned_data['about']
            with transaction.atomic():
                profile.save()
            return HttpResponseRedirect(reverse('profiles:profiles_view_profile', args=(profile.id,)))
        else:
            print(form.errors)
            return None
    else:
        form = EditProfileForm(
            initial={
                'about': profile.about,
            }
        )
        context = {
            'profile' : profile,
            'form' : form,
        }
        return render(request, 'profiles/edit_profile.html', context)

def accept_terms(request):
    profile = request.user.profile
    if (profile.confirmed_agreements):
        return HttpResponseRedirect(reverse('home'))
    if request.method == 'POST':
        form = AcceptTermsForm(request.POST)
        if form.is_valid():
            profile.confirmed_agreements = True
            profile.date_confirmed_agreements = timezone.now()
            with transaction.atomic():
                profile.save()
            return HttpResponseRedirect(reverse('home'))
        else:
            print(form.errors)
            return None
    else:
        form = AcceptTermsForm()
        context = {
            'form': form,
            "terms": TERMS,
            "eula": EULA,
            "privacy": PRIVACY,
        }
        return render(request, 'profiles/accept_terms.html', context)