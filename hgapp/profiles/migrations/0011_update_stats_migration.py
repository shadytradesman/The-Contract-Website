from django.db import migrations

from games.games_constants import get_completed_game_invite_excludes_query, get_completed_game_excludes_query
from games.models import WIN, LOSS, DEATH

from profiles.models import GM_PREFIX

def reverse_migrate_update_stats(apps, schema_editor):
    pass

def number_deaths(game):
    num_deaths = 0
    for attendance in game.game_attendance_set.all():
        if attendance.outcome == DEATH:
            num_deaths = num_deaths + 1
    return num_deaths


def number_victories(game):
    number_victories = 0
    for attendance in game.game_attendance_set.all():
        if attendance.outcome == WIN:
            number_victories = number_victories + 1
    return number_victories


def number_losses(game):
    num_losses = 0
    for attendance in game.game_attendance_set.all():
        if attendance.outcome == LOSS:
            num_losses = num_losses + 1
    return num_losses

def achieves_golden_ratio(game):
    death = False
    win = False
    for attendance in game.game_attendance_set.all():
        if attendance.outcome == WIN:
            win = True
        if attendance.outcome == DEATH:
            death = True
    return win and death

def at_least_one_death(game):
    for attendance in game.game_attendance_set.all():
        if attendance.outcome == DEATH:
            return True

def _player_prefix_from_counts(num_completed, num_deadly_games, num_deaths_on_games):
    if num_completed < 3:
        return "UNTESTED"
    game_deadliness = num_deadly_games/num_completed
    if num_deadly_games == 0 or game_deadliness < 0.07:
        # fewer than 1 in 14 games has PC death
        return "SHELTERED"
    # fewer than 1 in 6 games has PC death or hasn't been in 5 games where a Contractor died
    rarely_plays_in_deadly_games = game_deadliness < .16 or num_deadly_games < 5
    death_ratio = num_deaths_on_games / num_deadly_games
    if death_ratio < 0.2:
        return "DEVIOUS" if rarely_plays_in_deadly_games else "INGENIOUS"
    elif death_ratio < 0.5:
        return "RESOURCEFUL" if rarely_plays_in_deadly_games else "CALCULATING"
    else:
        return "UNLUCKY" if rarely_plays_in_deadly_games else "TORTURED"


def _player_suffix_from_num_games(num_completed):
    if num_completed < 5:
        return "NEWBIE"
    elif num_completed < 15:
        return "NOVICE"
    elif num_completed < 30:
        return "ADEPT"
    elif num_completed < 60:
        return "SEASONED"
    elif num_completed < 100:
        return "PROFESSIONAL"
    elif num_completed < 200:
        return "VETERAN"
    elif num_completed < 350:
        return "MASTER"
    else:
        return "GRANDMASTER"

def _gm_suffix_from_num_gm_games(num_gm_games):
    if num_gm_games < 1:
        return "SPECTATOR"
    elif num_gm_games < 5:
        return "REFEREE"
    elif num_gm_games < 15:
        return "MIDDLE_MANAGEMENT"
    elif num_gm_games < 30:
        return "BOSS"
    elif num_gm_games < 60:
        return "RULER"
    elif num_gm_games < 100:
        return "HARBINGER"
    else:
        return "GOD"

def _gm_prefix_from_stats(num_gm_games, num_killed_contractors):
    if num_gm_games == 0:
        return None
    kill_ratio = num_killed_contractors/num_gm_games
    if kill_ratio < 0.07:
        # pillowy
        return GM_PREFIX[0][0]
    elif kill_ratio < 0.15:
        # benevolent
        return GM_PREFIX[1][0]
    elif kill_ratio < 0.5:
        # just
        return GM_PREFIX[2][0]
    elif kill_ratio < 0.75:
        # Sadistic
        return GM_PREFIX[3][0]
    else:
        # Cruel
        return GM_PREFIX[4][0]

def migrate_update_stats(apps, schema_editor):
    Profile = apps.get_model('profiles', 'Profile')
    Game = apps.get_model('games', 'Game')
    for profile in Profile.objects.all():
        gm_games = Game.objects.filter(gm=profile.user).exclude(get_completed_game_excludes_query()) \
            .order_by("-end_time") \
            .all()
        num_gm_games = gm_games.count()
        num_gm_kills = 0
        num_golden_ratio_games = 0
        num_gm_victories = 0
        num_gm_losses = 0
        cells_gmed = set()
        contractors_gmed = set()
        players_gmed = set()
        for game in gm_games:
            num_gm_kills = num_gm_kills + number_deaths(game)
            num_gm_victories = num_gm_victories + number_victories(game)
            num_gm_losses = num_gm_losses + number_losses(game)
            if achieves_golden_ratio(game):
                num_golden_ratio_games = num_golden_ratio_games + 1
            if game.cell:
                cells_gmed.add(game.cell.id)
            for attendance in game.game_attendance_set.all():
                if attendance.attending_character:
                    contractors_gmed.add(attendance.attending_character.id)
                    players_gmed.add(attendance.attending_character.player.id)
        profile.num_gmed_players = len(players_gmed)
        profile.num_gmed_contractors = len(contractors_gmed)
        profile.num_gmed_cells = len(cells_gmed)
        profile.num_games_gmed = num_gm_games
        profile.num_gm_losses = num_gm_losses
        profile.num_gm_kills = num_gm_kills
        profile.num_gm_victories = num_gm_victories
        profile.num_golden_ratios = num_golden_ratio_games
        completed_game_invites = profile.user.game_invite_set \
            .exclude(get_completed_game_invite_excludes_query()) \
            .exclude(is_declined=True) \
            .order_by("-relevant_game__end_time") \
            .all()
        profile.num_player_games = completed_game_invites.count()
        invites_with_death = [invite for invite in completed_game_invites
                              if invite.attendance
                              and invite.attendance.attending_character
                              and at_least_one_death(invite.relevant_game)]
        profile.num_deadly_player_games = len(invites_with_death)
        played_character_ids = set()
        num_deaths = 0
        num_victories = 0
        num_losses = 0
        num_played_ringers = 0
        for invite in completed_game_invites:
            if invite.attendance:
                if invite.attendance.attending_character:
                    played_character_ids.add(invite.attendance.attending_character.id)
                if invite.attendance.outcome == WIN:
                    num_victories = num_victories + 1
                elif invite.attendance.outcome == LOSS:
                    num_losses = num_losses + 1
                elif invite.attendance.outcome == DEATH:
                    num_deaths = num_deaths + 1
            else:
                num_played_ringers = num_played_ringers + 1
        profile.num_contractors_played = len(played_character_ids)
        profile.num_player_deaths = num_deaths
        profile.num_player_victories = num_victories
        profile.num_player_losses = num_losses
        profile.num_played_ringers = num_played_ringers
        profile.num_player_survivals = profile.num_deadly_player_games - num_deaths
        profile.player_prefix = _player_prefix_from_counts(profile.num_player_games, profile.num_deadly_player_games, profile.num_player_deaths)
        profile.player_suffix = _player_suffix_from_num_games(profile.num_player_games)
        profile.gm_prefix = _gm_prefix_from_stats(profile.num_games_gmed, profile.num_gm_kills)
        profile.gm_suffix = _gm_suffix_from_num_gm_games(profile.num_games_gmed)
        profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_auto_20210904_2023'),
    ]

    operations = [
        migrations.RunPython(migrate_update_stats, reverse_migrate_update_stats),
    ]

