from django.db import migrations, models


WIN = 'WIN'
LOSS = 'LOSS'
DEATH = 'DEATH'
DECLINED = 'DECLINED'
RINGER_VICTORY = 'RINGER_VICTORY'
RINGER_FAILURE = 'RINGER_FAILURE'

EXP_MVP = "MVP"
EXP_LOSS_V1 = "LOSS_V1"
EXP_LOSS_RINGER_V1 = "LOSS_RINGER_V1"
EXP_WIN_V1 = "WIN_V1"
EXP_WIN_RINGER_V1 = "WIN_RINGER_V1"
EXP_LOSS_V2 = "LOSS_V2"
EXP_LOSS_RINGER_V2 = "LOSS_RINGER_V2"
EXP_WIN_V2 = "WIN_V2"
EXP_WIN_RINGER_V2 = "WIN_RINGER_V2"
EXP_IN_WORLD_GAME = "IN_WORLD"
EXP_GM = "GM"
EXP_JOURNAL = "JOURNAL"
EXP_CUSTOM = "CUSTOM"

def reverse_migrate_update_stats(apps, schema_editor):
    pass

def migrate_update_stats(apps, schema_editor):
    ExperienceReward = apps.get_model('characters', 'ExperienceReward')
    for exp_reward in ExperienceReward.objects.all():
        set_type(exp_reward)
        exp_reward.save()

def set_type(reward):
    if hasattr(reward, 'custom_reason') and reward.custom_reason:
        reward.type = EXP_CUSTOM
    elif hasattr(reward, 'game'):
        reward.type = EXP_GM
    elif hasattr(reward, 'journal'):
        reward.type = EXP_JOURNAL
    elif hasattr(reward, 'game_attendance'):
        attendance = reward.game_attendance
        if is_victory(attendance):
            reward.type = EXP_WIN_V1
        elif is_loss(attendance):
            reward.type = EXP_LOSS_V1
        elif is_ringer_victory(attendance):
            reward.type = EXP_WIN_RINGER_V1
        elif is_ringer_failure(attendance):
            reward.type = EXP_LOSS_RINGER_V1
        else:
            reward.type = EXP_CUSTOM
            reward.custom_reason = "glitched exp reward"
            reward.custom_value = 0
            reward.is_void = True
    else:
        reward.type = EXP_CUSTOM
        reward.custom_reason = "glitched exp reward"
        reward.custom_value = 0
        reward.is_void = True

def is_victory(attendance):
    return attendance.outcome == WIN

def is_loss(attendance):
    return attendance.outcome == LOSS

def is_death(attendance):
    return attendance.outcome == DEATH

def is_ringer_victory(attendance):
    return attendance.outcome == RINGER_VICTORY

def is_ringer_failure(attendance):
    return attendance.outcome == RINGER_FAILURE

class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0051_auto_20211113_1759'),
    ]

    operations = [
        migrations.RunPython(migrate_update_stats, reverse_migrate_update_stats),
    ]
