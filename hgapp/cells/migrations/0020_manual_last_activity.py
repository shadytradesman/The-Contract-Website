from django.db import migrations, models
from django.db.models import Q
from django.conf import settings
from django.db import transaction
from django.conf import settings

def migrate_last_activity(apps, schema_editor):
    CellMembership = apps.get_model('cells', 'CellMembership')
    WorldEvent = apps.get_model('cells', 'WorldEvent')
    for membership in CellMembership.objects.all():
        print("processing membership {}".format(membership.pk))
        latest_date = membership.joined_date

        latest_played = membership.member_player.game_invite_set\
            .filter(is_declined=False)\
            .filter(relevant_game__cell=membership.relevant_cell)\
            .exclude(get_completed_relevant_game_excludes_query())\
            .order_by('-relevant_game__end_time').first()
        if latest_played is not None and latest_played.relevant_game.end_time:
            if latest_played.relevant_game.end_time > latest_date:
                latest_date = latest_played.relevant_game.end_time

        latest_gmed = membership.relevant_cell.game_set \
            .filter(gm=membership.member_player) \
            .exclude(get_completed_game_excludes_query()) \
            .order_by('-end_time').first()
        if latest_gmed is not None and latest_gmed.end_time:
            if latest_gmed.end_time > latest_date:
                latest_date = latest_gmed.end_time

        latest_event = WorldEvent.objects.filter(creator=membership.member_player).filter(parent_cell=membership.relevant_cell)\
            .order_by('-created_date').first()
        if latest_event:
            if latest_event.created_date > latest_date:
                latest_date = latest_event.created_date

        membership.last_activity = latest_date
        membership.save()

def reverse_mig(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0019_cellmembership_last_activity'),
    ]

    operations = [
        migrations.RunPython(migrate_last_activity, reverse_mig),
    ]


### COPIED CODE FROM GAME CONSTANTS FOR MIGRATION

# This is the ID of the game when experience was changed for the November 2021 update.
EXP_V1_V2_GAME_ID = 567 if not settings.DEBUG else 0

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


def get_completed_game_excludes_query():
    return Q(status=GAME_STATUS[0][0]) \
           | Q(status=GAME_STATUS[1][0]) \
           | Q(status=GAME_STATUS[4][0])


def get_completed_relevant_game_excludes_query():
    return Q(relevant_game__status=GAME_STATUS[0][0]) \
           | Q(relevant_game__status=GAME_STATUS[1][0]) \
           | Q(relevant_game__status=GAME_STATUS[4][0])

def get_scheduled_game_excludes_query():
    return Q(status=GAME_FINISHED) \
           | Q(status=GAME_ARCHIVED) \
           | Q(status=GAME_CANCELED) \
           | Q(status=GAME_VOID) \
           | Q(status=GAME_RECORDED)


def get_completed_game_invite_excludes_query():
    return Q(relevant_game__status=GAME_STATUS[0][0]) \
           | Q(relevant_game__status=GAME_STATUS[1][0]) \
           | Q(relevant_game__status=GAME_STATUS[4][0])
