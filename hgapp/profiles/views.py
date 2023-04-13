from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.db import transaction
from django.utils import timezone
from collections import defaultdict
from heapq import merge


from profiles.forms import EditProfileForm, AcceptTermsForm
from profiles.models import Profile
from info.terms import EULA, TERMS, PRIVACY
from games.games_constants import get_completed_game_invite_excludes_query, get_completed_game_excludes_query, GAME_STATUS

def key_funct(x):
    return x[0]

class ProfileView(generic.DetailView):
    template_name = 'profiles/view_profile.html'

    def get_queryset(self):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        self.cells = self.profile.user.cell_set.filter(cellmembership__is_banned=False).all()

        characters = self.profile.user.character_set.filter(is_deleted=False)
        if self.profile.user != self.request.user:
            characters = characters.filter(private=False)
        characters = characters.order_by('-edit_date').all()
        self.scenarios = []
        if self.request.user.is_authenticated:
            self.scenarios = self.request.user.scenario_discovery_set\
                .filter(relevant_scenario__creator=self.profile.user).all()
        self.living_characters = [character for character in characters if not character.is_dead]
        self.deceased_characters = [character for character in characters if character.is_dead]

        self.attended_games = self.profile.user.game_set.exclude(get_completed_game_excludes_query()).all()

        return Profile.objects

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)

        context = self.populate_contractor_stats_context(context)
        context = self.populate_gm_stats_context(context)

        context['profile'] = self.profile
        context['cells'] = self.cells
        context['living_characters'] = self.living_characters
        context['deceased_characters'] = self.deceased_characters
        context['scenarios'] = self.scenarios
        context['attended_games'] = self.attended_games
        context['profile_view'] = True
        context['profile_viewable'] = self.profile.player_can_view(self.request.user)
        return context

    def populate_contractor_stats_context(self, context):
        context['num_games_played'] = self.profile.num_player_games
        context['num_contractors_played'] = self.profile.num_contractors_played
        context['num_contractor_deaths'] = self.profile.num_player_deaths
        context['num_contractor_victories'] = self.profile.num_player_victories
        context['num_contractor_losses'] = self.profile.num_player_losses
        context['num_deadly_games_survived'] = self.profile.num_player_survivals
        return context

    def populate_gm_stats_context(self, context):
        context['num_gm_games'] = self.profile.num_games_gmed
        context['num_gm_moves'] = self.profile.num_moves_gmed
        context['num_cells_gmed'] = self.profile.num_gmed_cells
        context['num_contractors_gmed'] = self.profile.num_gmed_contractors
        context['num_players_gmed'] = self.profile.num_gmed_players
        context['num_gm_kills'] = self.profile.num_gm_kills
        context['num_golden_ratio_games'] = self.profile.num_golden_ratios
        context['num_gm_victories'] = self.profile.num_gm_victories
        context['num_gm_losses'] = self.profile.num_gm_losses
        return context

class ProfileTimelineView(generic.DetailView):
    template_name = 'profiles/contract_record_snip.html'

    def get_queryset(self):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        self.cells = self.profile.user.cell_set.filter(cellmembership__is_banned=False).all()

        self.completed_game_invites = self.profile.completed_game_invites()
        self.gmed_games = self.profile.get_games_where_player_gmed()
        self.gmed_moves = self.profile.get_moves_where_player_gmed()

        played_games_by_date = [(x.relevant_game.end_time, "play", x) for x in self.completed_game_invites]
        gmed_games_by_date = [(x.end_time, "gm", x) for x in self.gmed_games]
        gmed_moves_by_date = [(x.created_date, "move", x) for x in self.gmed_moves]

        events_by_date = list(merge(played_games_by_date, gmed_games_by_date, gmed_moves_by_date, reverse=True))
        timeline = defaultdict(list)
        for event in events_by_date:
            timeline[event[0].strftime("%d %b %Y")].append((event[1], event[2]))

        self.game_timeline = dict(timeline)
        self.attended_games = self.profile.user.game_set.exclude(get_completed_game_excludes_query()).all()

        return Profile.objects

    def get_context_data(self, **kwargs):
        context = super(ProfileTimelineView, self).get_context_data(**kwargs)

        context['profile'] = self.profile
        context['game_timeline'] = self.game_timeline
        context['profile_view'] = True
        return context

def profile_edit(request):
    profile = get_object_or_404(Profile, pk=request.user.pk)
    if request.method == 'POST':
        form = EditProfileForm(request.POST)
        if form.is_valid():
            profile.about = form.cleaned_data['about']
            with transaction.atomic():
                profile.is_private = form.cleaned_data['private_profile']
                profile.hide_fake_ads = form.cleaned_data['hide_fake_ads']
                profile.save()
                profile.update_view_adult_content(form.cleaned_data['view_adult'])
            return HttpResponseRedirect(reverse('profiles:profiles_view_profile', args=(profile.id,)))
        else:
            print(form.errors)
            return None
    else:
        form = EditProfileForm(
            initial={
                'about': profile.about,
                'view_adult': profile.view_adult_content,
                'hide_fake_ads': profile.hide_fake_ads,
                'private_profile': profile.is_private,
            }
        )
        context = {
            'profile': profile,
            'form': form,
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