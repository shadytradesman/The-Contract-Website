from django.db.models import Q

# This is the ID of the game when experience was changed for the November 2021 update.
# EXP_V1_V2_GAME_ID = 567
EXP_V1_V2_GAME_ID = 5

GAME_STATUS = (
    # Invites go out, players may accept invites w/ characters and change whether they are coming and with which character
    # The scenario is chosen
    # GM specifies level, message, etc.
    ('SCHEDULED', 'Scheduled'),

    # The game is "activated". invites are invalidated. Players can no longer change which character is attending
    # Characters are closed for editing for the duration of the game
    # GMs have 24 hours from this point to declare the game finished, or individual players may void their attendance.
    ('ACTIVE', 'Active'),

    # Game is finished, GM declares all outcomes, characters are unlocked or declared dead. Game is officially over
    # Void proceedings may occur. Players may open game for void vote.
    # Characters are locked while a void vote is in progress.
    # Void votes may only last 24 hours
    # GM may declare void.
    ('FINISHED', 'Finished'),

    # After a set time peroid, or after any character is attending another game that is in the "ACTIVE" state, the void window
    # is closed. The game transitions into "ARCHIVED."
    ('ARCHIVED', 'Archived'),

    # Any game that is scheduled, can be canceled, which is an end state. All invites are voided. Attendances are erased.
    ('CANCELED', 'Canceled'),

    # All games that reach the "Active" state can be voided through verious means. Attendance remains on record, but is void.
    ('VOID', 'Void'),

    # Finalized games that were entered after-the-fact.
    ('RECORDED', 'Archived'),
)

def get_completed_game_excludes_query():
    return Q(status=GAME_STATUS[0][0]) \
            | Q(status=GAME_STATUS[1][0]) \
            | Q(status=GAME_STATUS[4][0])

def get_completed_game_invite_excludes_query():
    return Q(relevant_game__status=GAME_STATUS[0][0]) \
             | Q(relevant_game__status=GAME_STATUS[1][0]) \
             | Q(relevant_game__status=GAME_STATUS[4][0])
