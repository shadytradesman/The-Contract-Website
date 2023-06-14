from collections import defaultdict
from django.core.cache import cache

from .models import Game_Attendance


# Get the contractor's contacts. Returns a mapping from contractor to a list of tuples of games they were encountered on
def get_character_contacts(character):
    cache_key = "contractor_contacts" + str(character.pk)
    sentinel = object()
    cache_contents = cache.get(cache_key, sentinel)
    if cache_contents is sentinel:
        contacts = __inner_get_character_contacts(character)
        cache.set(cache_key, contacts, timeout=30)
        return contacts
    else:
        return cache.get(cache_key)


def __inner_get_character_contacts(character):
    game_ids = character.game_attendance_set.exclude(outcome=None).exclude(is_confirmed=False).order_by("relevant_game__end_time").values_list('relevant_game__id', flat=True).all()
    game_number = {}
    for i, game_id in enumerate(game_ids):
        game_number[game_id] = i + 1
    attendances = Game_Attendance.objects.select_related("relevant_game").select_related("attending_character").filter(relevant_game__id__in=game_ids, is_confirmed=True, attending_character__isnull=False).order_by("relevant_game__end_time")
    games_by_character = defaultdict(list)
    for attendance in attendances:
        if hasattr(attendance, "attending_character") and attendance.attending_character:
            if not attendance.attending_character == character and not attendance.attending_character.is_deleted:
                games_by_character[attendance.attending_character].append((game_number[attendance.relevant_game.id], attendance.relevant_game))
    return games_by_character


