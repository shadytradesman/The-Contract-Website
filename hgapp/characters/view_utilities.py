from journals.models import Journal
from hgapp.utilities import get_object_or_none

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
            downtime_journal = get_object_or_none(Journal, game_attendance=attendance, is_downtime=True)
            if not downtime_journal:
                chosen_attendance = attendance
                is_downtime = True
    if chosen_attendance:
        reward_is_improvement = Journal.get_num_journals_until_improvement(character) <= 1
        return {"attendance": chosen_attendance, "is_downtime": is_downtime, "reward_is_improvement": reward_is_improvement}
    else:
        return None
