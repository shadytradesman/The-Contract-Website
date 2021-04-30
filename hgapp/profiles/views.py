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
from characters.models import Character
from games.models import Game, DISCOVERY_REASON
from info.terms import EULA, TERMS, PRIVACY
from games.games_constants import get_completed_game_invite_excludes_query, get_completed_game_excludes_query, GAME_STATUS

class ProfileView(generic.DetailView):
    template_name = 'profiles/view_profile.html'

    def get_queryset(self):
        self.profile = get_object_or_404(Profile, pk=self.kwargs['pk'])
        self.cells = self.profile.user.cell_set.all()

        characters = self.profile.user.character_set.filter(is_deleted=False)
        if self.profile.user != self.request.user:
            characters = characters.filter(private=False)
        characters = characters.order_by('-edit_date').all()
        self.scenarios = []
        if self.request.user.is_authenticated:
            self.scenarios = self.request.user.scenario_discovery_set\
                .filter(relevant_scenario__creator=self.profile.user).all()
        self.living_characters = [character for character in characters if not character.is_dead()]
        self.deceased_characters = [character for character in characters if character.is_dead()]

        self.completed_game_invites = self.profile.completed_game_invites()
        self.completed_games = self.profile.get_games_where_player_gmed()

        played_games_by_date = [(x.relevant_game.end_time, "play", x) for x in self.completed_game_invites]
        gmed_games_by_date = [(x.end_time, "gm", x) for x in self.completed_games]

        events_by_date = list(merge(played_games_by_date, gmed_games_by_date))
        timeline = defaultdict(list)
        for event in events_by_date:
            timeline[event[0].strftime("%d %b %Y")].append((event[1], event[2]))

        self.game_timeline = dict(timeline)
        self.games_gmed = Game.objects.filter(gm=self.profile.user).exclude(get_completed_game_excludes_query()).all()
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
        context['gmed_games'] = self.games_gmed
        context['attended_games'] = self.attended_games
        context['game_timeline'] = self.game_timeline
        context['profile_view'] = True
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

    def populate_gm_stats_context(self, context):
        cells_gmed = set()
        contractors_gmed = set()
        players_gmed = set()
        num_gm_kills = 0
        num_golden_ratio_games = 0
        num_gm_victories = 0
        num_gm_losses = 0
        for game in self.games_gmed:
            num_gm_kills = num_gm_kills + game.number_deaths()
            num_gm_victories = num_gm_victories + game.number_victories()
            num_gm_losses = num_gm_losses + game.number_losses()
            if game.cell:
                cells_gmed.add(game.cell.id)
            for attendance in game.game_attendance_set.all():
                if attendance.attending_character:
                    contractors_gmed.add(attendance.attending_character.id)
                    players_gmed.add(attendance.attending_character.player.id)
            if game.achieves_golden_ratio():
                num_golden_ratio_games = num_golden_ratio_games + 1
        context['num_gm_games'] = self.games_gmed.count()
        context['num_cells_gmed'] = len(cells_gmed)
        context['num_contractors_gmed'] = len(contractors_gmed)
        context['num_players_gmed'] = len(players_gmed)
        context['num_gm_kills'] = num_gm_kills
        context['num_golden_ratio_games'] = num_golden_ratio_games
        context['num_gm_victories'] = num_gm_victories
        context['num_gm_losses'] = num_gm_losses
        return context


def profile_edit(request):
    profile = get_object_or_404(Profile, pk=request.user.pk)
    if request.method == 'POST':
        form = EditProfileForm(request.POST)
        if form.is_valid():
            profile.about = form.cleaned_data['about']
            with transaction.atomic():
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