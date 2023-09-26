from journals.models import Journal
from questionnaire.models import Question, Answer
from hgapp.utilities import get_object_or_none
from .models import Weapon, EXP_REWARD_VALUES, EXP_QUESTIONNAIRE_INITIAL
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


def does_character_have_outstanding_questions(character):
    game_number = character.number_completed_games()
    num_answered_questions = Answer.objects.filter(relevant_character=character, is_valid=True).count()
    num_questions_available = Question.objects.exclude(contract_number__gt=game_number).count()
    if num_answered_questions < num_questions_available:
        return True
    num_unique_questions = Question.objects.count()
    if num_answered_questions >= num_unique_questions:
        # They've gone through all questions at least once. Got to check repeats.
        num_repeatable_questions = Question.objects.filter(is_repeatable=True).count()
        if num_answered_questions >= num_unique_questions + num_repeatable_questions:
            # Character has completely finished questionnaire including all repeats
            return False
        num_repeatable_answers = Answer.objects\
            .filter(relevant_character=character,
                    is_valid=True,
                    question__is_repeatable=True,
                    written_contract_number__lt=game_number-9)\
            .count()
        if num_answered_questions < num_repeatable_answers + num_unique_questions:
            # There are outstanding repeatable questions
            return True
    return False


def next_question_reward(character):
    next_reward_type = "Exp"
    next_reward_quantity = 2
    num_answered_questions = Answer.objects.filter(is_valid=True, relevant_character=character).count()
    if num_answered_questions < 5:
        next_reward_quantity = EXP_REWARD_VALUES[EXP_QUESTIONNAIRE_INITIAL]
    elif num_answered_questions >= 5:
        if (num_answered_questions - 5) % 10 < 2:
            next_reward_type = "Improvement"
            next_reward_quantity = 1
    return "{} {}".format(next_reward_quantity, next_reward_type)


def get_world_element_default_dict(world_element_cell_choices):
    # It is important that cells that may not /yet/ have elements in them be included.
    if world_element_cell_choices:
        return defaultdict(list, {k: [] for k in world_element_cell_choices})
    else:
        return defaultdict(list)


def get_weapons_by_type():
    weapons = Weapon.objects.order_by("type", "bonus_damage").all()
    weapons_by_type = defaultdict(list)
    for weapon in weapons:
        weapons_by_type[weapon.get_type_cat()].append(weapon)
    return dict(weapons_by_type)
