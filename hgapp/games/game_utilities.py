from collections import defaultdict

from games.models import Game_Attendance


def get_character_contacts(character):
    game_ids = character.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("relevant_game__end_time").values_list('relevant_game__id', flat=True).all()
    game_number = {}
    for i, game_id in enumerate(game_ids):
        game_number[game_id] = i + 1
    attendances = Game_Attendance.objects.filter(relevant_game__id__in=game_ids, is_confirmed=True).order_by("relevant_game__end_time")
    games_by_character = defaultdict(list)
    for attendance in attendances:
        if hasattr(attendance, "attending_character") and attendance.attending_character:
            if not attendance.attending_character == character:
                games_by_character[attendance.attending_character].append((game_number[attendance.relevant_game.id], attendance.relevant_game))
    return games_by_character


