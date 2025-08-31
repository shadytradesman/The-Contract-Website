from django.db import migrations, models
from django.db import transaction
from django.db.models import Q, Count
from collections import defaultdict
from django.utils import timezone

def get_completed_game_excludes_query():
    return Q(status=GAME_STATUS[0][0]) \
            | Q(status=GAME_STATUS[1][0]) \
            | Q(status=GAME_STATUS[4][0])

def correct_source_cell_for_improvement(improvement):
    if not improvement.is_improvement:
        raise ValueError("This isn't an improvement")
    if improvement.is_gm_reward:
        improvement.source_cell = improvement.relevant_game.cell
    elif improvement.relevant_scenario_id:
        finished_game = improvement.relevant_scenario.game_set.exclude(get_completed_game_excludes_query()).order_by("created_date").first()
        if finished_game is None:
            raise ValueError("No finished game for scenario granting reward")
        improvement.source_cell_id = finished_game.cell_id
    improvement.save()

def get_source_cell(exp_reward):
    if exp_reward.type == EXP_GM:
        return exp_reward.game.cell
    if exp_reward.type in [EXP_GM_NEW_PLAYER, EXP_GM_RATIO]:
        return exp_reward.game.cell
    if exp_reward.type in [EXP_GM_MOVE, EXP_GM_MOVE_V2]:
        return exp_reward.move.cell
    if hasattr(exp_reward, 'game_attendance'):
        return exp_reward.game_attendance.relevant_game.cell


def migrate_reward_in_cell(apps, schema_editor):
    Reward = apps.get_model('games', 'Reward')
    ExperienceReward = apps.get_model('characters', 'ExperienceReward')
    with transaction.atomic():
        count = 0
        for improvement in Reward.objects.filter(is_void=False).exclude(is_improvement=False).select_related("relevant_game", "relevant_scenario"):
            correct_source_cell_for_improvement(improvement)
            if improvement.source_cell_id is not None:
                count += 1
        print("Finished improvements. Updated {}".format(count))
    with transaction.atomic():
        count = 0
        for exp_reward in ExperienceReward.objects.filter(type__in=[EXP_GM, EXP_GM_MOVE_V2, EXP_GM_MOVE, EXP_GM_RATIO, EXP_GM_NEW_PLAYER]).exclude(is_void=True).all():
            exp_reward.source_cell = get_source_cell(exp_reward)
            if exp_reward.source_cell_id is not None:
                exp_reward.save()
                count += 1
        print("Finished exp rewards. Updated {}".format(count))

def reverse_migrate_reward_in_cell(apps, schema_editor):
    print("Finished reverse")


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0074_reward_source_cell'),
        ('characters', '0110_experiencereward_source_cell'),
    ]

    operations = [
        migrations.RunPython(migrate_reward_in_cell, reverse_migrate_reward_in_cell),
    ]

GAME_SCHEDULED = 'SCHEDULED'
GAME_ACTIVE = 'ACTIVE'
GAME_RECORDED = 'RECORDED'
GAME_VOID = 'VOID'
GAME_CANCELED = 'CANCELED'
GAME_ARCHIVED = 'ARCHIVED'
GAME_FINISHED = 'FINISHED'

GAME_STATUS = (
    # Invites go out, players may accept invites w/ characters and change whether they are coming and with which character
    # The scenario is chosen
    # GM specifies level, message, etc.
    (GAME_SCHEDULED, 'Scheduled'),

    # The game is "activated". invites are invalidated. Players can no longer change which character is attending
    # Characters are closed for editing for the duration of the game
    # GMs have 24 hours from this point to declare the game finished, or individual players may void their attendance.
    (GAME_ACTIVE, 'Active'),

    # Game is finished, GM declares all outcomes, characters are unlocked or declared dead. Game is officially over
    # Void proceedings may occur. Players may open game for void vote.
    # Characters are locked while a void vote is in progress.
    # Void votes may only last 24 hours
    # GM may declare void.
    (GAME_FINISHED, 'Finished'),

    # After a set time peroid, or after any character is attending another game that is in the "ACTIVE" state, the void window
    # is closed. The game transitions into "ARCHIVED."
    (GAME_ARCHIVED, 'Archived'),

    # Any game that is scheduled, can be canceled, which is an end state. All invites are voided. Attendances are erased.
    (GAME_CANCELED, 'Canceled'),

    # All games that reach the "Active" state can be voided through verious means. Attendance remains on record, but is void.
    (GAME_VOID, 'Void'),

    # Finalized games that were entered after-the-fact.
    (GAME_RECORDED, 'Archived'),
)

EXP_MVP = "MVP"
EXP_LOSS_V1 = "LOSS_V1"
EXP_LOSS_RINGER_V1 = "LOSS_RINGER_V1"
EXP_WIN_V1 = "WIN_V1"
EXP_WIN_RINGER_V1 = "WIN_RINGER_V1"
EXP_LOSS_V2 = "LOSS_V2"
EXP_LOSS_V3 = "LOSS_V3" # Same as loss V2 but with more out of playgroup bonus
EXP_LOSS_IN_WORLD_V2 = "LOSS_IN_WORLD_V2"
EXP_LOSS_RINGER_V2 = "LOSS_RINGER_V2"
EXP_WIN_V2 = "WIN_V2"
EXP_WIN_V3 = "WIN_V3" # Same as win V2 but with more out of playgroup bonus
EXP_WIN_IN_WORLD_V2 = "WIN_IN_WORLD_V2"
EXP_WIN_RINGER_V2 = "WIN_RINGER_V2"
EXP_GM = "GM"
EXP_GM_RATIO = "GM_GOLDEN_RATIO"
EXP_GM_NEW_PLAYER = "GM_NEW_PLAYER"
EXP_GM_MOVE = "GM_MOVE"
EXP_GM_MOVE_V2 = "GM_MOVE_V2"
EXP_JOURNAL = "JOURNAL"
EXP_CUSTOM = "CUSTOM"
EXP_EXCHANGE = "Exchange"
