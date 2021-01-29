from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.db import transaction
from django.utils import timezone


from profiles.forms import EditProfileForm, AcceptTermsForm
from profiles.models import Profile
from characters.models import Character
from info.terms import EULA, TERMS, PRIVACY

class ProfileView(generic.DetailView):
    template_name = 'profiles/view_profile.html'

    def get_queryset(self):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        self.cells = self.profile.user.cell_set.all()
        if self.profile.user == self.request.user:
            self.characters = self.profile.user.character_set.filter(is_deleted=False).order_by('-edit_date').all()
        else:
            self.characters = self.profile.user.character_set.filter(private=False, is_deleted=False).order_by('-edit_date').all()
        self.completed_game_invites = self.profile.completed_game_invites()
        return Profile.objects

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        self.profile.recompute_titles() #TODO: Delete this any time after Feb 2021 for a big perf boost.

        context = self.populate_contractor_stats_context(context)

        context['profile'] = self.profile
        context['cells'] = self.cells
        context['characters'] = self.characters
        return context

    def populate_contractor_stats_context(self, context):
        context['num_games_played'] = self.completed_game_invites.count()
        played_character_ids = set()
        num_deaths = 0
        num_victories = 0
        num_losses = 0
        for invite in self.completed_game_invites:
            if invite.attendance:
                if invite.attendance.attending_character:
                    played_character_ids.add(invite.attendance.attending_character.id)
                if invite.attendance.is_victory():
                    num_victories = num_victories + 1
                elif invite.attendance.is_loss():
                    num_losses = num_losses + 1
                elif invite.attendance.is_death():
                    num_deaths = num_deaths + 1
        num_contractors_played = len(played_character_ids)
        context['num_contractors_played'] = num_contractors_played
        context['num_contractor_deaths'] = num_deaths
        context['num_contractor_victories'] = num_victories
        context['num_contractor_losses'] = num_losses
        invites_with_a_death = self.profile.get_invites_with_death(self.completed_game_invites)
        invites_where_player_died = self.profile.get_invites_where_player_died(invites_with_a_death)
        context['num_deadly_games_survived'] = len(invites_with_a_death) - len(invites_where_player_died)
        return context


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