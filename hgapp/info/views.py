from django.shortcuts import render
from .terms import EULA, TERMS, PRIVACY
from info.models import FrontPageInfo
from profiles.models import Profile
from characters.models import CharacterTutorial, Ability, Character

def getting_started(request):
    return render(request, 'info/getting_started.html')

def terms(request):
    context= {
        "terms": TERMS,
        "eula": EULA,
        "privacy": PRIVACY,
    }
    return render(request, 'info/terms.html', context)

def probability(request):
    return render(request, 'info/probability.html')

def fiction(request):
    info = FrontPageInfo.objects.first()
    context= {
        "info": info,
    }
    return render(request, 'info/fiction.html', context)

def leaderboard(request):
    num_to_fetch = 10
    top_gms = Profile.objects.order_by('-num_games_gmed')[:num_to_fetch]
    deadliest_gms = Profile.objects.order_by('-num_gm_kills')[:num_to_fetch]
    most_social_gms = Profile.objects.order_by('-num_gmed_players')[:num_to_fetch]

    top_players = Profile.objects.order_by('-num_player_games')[:num_to_fetch]
    top_ringer_players = Profile.objects.order_by('-num_played_ringers')[:num_to_fetch]
    top_survivors = Profile.objects.order_by('-num_player_survivals')[:num_to_fetch]

    top_contractor_wins = Character.objects.order_by('-num_victories')[:num_to_fetch]
    top_contractor_losses = Character.objects.order_by('-num_losses')[:num_to_fetch]
    top_contractor_journals = Character.objects.order_by('-num_journals')[:num_to_fetch]

    context= {
        "top_players": top_players,
        "top_ringer_players": top_ringer_players,
        "top_survivors": top_survivors,

        "top_gms": top_gms,
        "deadliest_gms": deadliest_gms,
        "most_social_gms": most_social_gms,

        "top_contractor_wins": top_contractor_wins,
        "top_contractor_losses": top_contractor_losses,
        "top_contractor_journals": top_contractor_journals,

    }
    return render(request, 'info/leaderboard/leaderboard.html', context)
