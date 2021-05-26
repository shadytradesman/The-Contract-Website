from journals.models import Journal
from hgapp.utilities import get_object_or_none
from collections import defaultdict

# If applicable, returns an object containing info about what journal a character can write for a reward.
def get_characters_next_journal_credit(character):
    chosen_attendance = None
    is_downtime = False
    attendances_without_game_journals = character.game_attendance_set \
        .filter(relevant_game__end_time__isnull=False, journal__isnull=True) \
        .order_by("relevant_game__end_time") \
        .all()
    for attendance in attendances_without_game_journals:
        if attendance.is_confirmed and (attendance.relevant_game.is_finished() or attendance.relevant_game.is_recorded()):
            chosen_attendance = attendance
    if not chosen_attendance:
        completed_attendances = character.completed_games_rev_sort()
        for attendance in completed_attendances:
            downtime_journal = Journal.objects.filter(game_attendance=attendance, is_downtime=True).first()
            if not downtime_journal:
                chosen_attendance = attendance
                is_downtime = True
    if chosen_attendance:
        reward_is_improvement = Journal.get_num_journals_until_improvement(character) <= 1 and not is_downtime
        return {"attendance": chosen_attendance, "is_downtime": is_downtime, "reward_is_improvement": reward_is_improvement}
    else:
        return None

def get_world_element_default_dict(world_element_cell_choices):
    # It is important that cells that may not /yet/ have elements in them be included.
    return defaultdict(list, {k: [] for k in world_element_cell_choices if world_element_cell_choices})


