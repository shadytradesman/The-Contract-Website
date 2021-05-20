import cells.models

# Provided for reference only
#ROLE = (
#    ('LEADER', 'Leader'),
#    ('JUDGE', 'Judge'),
#    ('MEMBER', 'Member'),
#    ('WATCHER', 'Watcher'),
#)

def default_manage_memberships(role):
    if role == cells.models.ROLE[0][0]:
        return True
    if role == cells.models.ROLE[1][0]:
        return True
    if role == cells.models.ROLE[2][0]:
        return False
    if role == cells.models.ROLE[3][0]:
        return False
    raise ValueError('invalid role')

def default_manage_roles(role):
    if role == cells.models.ROLE[0][0]:
        return True
    if role == cells.models.ROLE[1][0]:
        return True
    if role == cells.models.ROLE[2][0]:
        return True
    if role == cells.models.ROLE[3][0]:
        return False
    raise ValueError('invalid role')

def default_post_events(role):
    if role == cells.models.ROLE[0][0]:
        return True
    if role == cells.models.ROLE[1][0]:
        return True
    if role == cells.models.ROLE[2][0]:
        return True
    if role == cells.models.ROLE[3][0]:
        return False
    raise ValueError('invalid role')

def default_manage_characters(role):
    if role == cells.models.ROLE[0][0]:
        return True
    if role == cells.models.ROLE[1][0]:
        return True
    if role == cells.models.ROLE[2][0]:
        return False
    if role == cells.models.ROLE[3][0]:
        return False
    raise ValueError('invalid role')

def default_edit_world(role):
    if role == cells.models.ROLE[0][0]:
        return True
    if role == cells.models.ROLE[1][0]:
        return True
    if role == cells.models.ROLE[2][0]:
        return False
    if role == cells.models.ROLE[3][0]:
        return False
    raise ValueError('invalid role')


def default_manage_games(role):
    if role == cells.models.ROLE[0][0]:
        return True
    if role == cells.models.ROLE[1][0]:
        return True
    if role == cells.models.ROLE[2][0]:
        return False
    if role == cells.models.ROLE[3][0]:
        return False
    raise ValueError('invalid role')