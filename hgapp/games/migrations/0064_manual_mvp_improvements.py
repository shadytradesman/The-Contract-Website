from django.db import migrations, models
from django.db import transaction
from django.utils import timezone

def migrate_mvp_improvement(apps, schema_editor):
    Reward = apps.get_model('games', 'Reward')
    Game_Attendance = apps.get_model('games', 'Game_Attendance')
    Character = apps.get_model('characters', 'Character')
    with transaction.atomic():
        for character in Character.objects.all():
            count = 0
            for attendance in Game_Attendance.objects.filter(is_confirmed=True, is_mvp=True, attending_character=character).exclude(outcome=None):
                count += 1
                if count % 3 == 0:
                    mvp_reward = Reward(relevant_game=attendance.relevant_game,
                                        rewarded_character=character,
                                        rewarded_player=character.player,
                                        is_improvement=True,
                                        is_MVP=True,
                                        awarded_on=timezone.now())
                    mvp_reward.save()
                    print("Rewarding {}".format(character.name))
        print("finished")

def reverse_migrate_mvp_improvement(apps, schema_editor):
    Reward = apps.get_model('games', 'Reward')
    rewards = Reward.objects.filter(is_MVP=True).all()
    for reward in rewards:
        reward.delete()
    print("Finished reverse")


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0063_reward_is_mvp'),
    ]

    operations = [
        migrations.RunPython(migrate_mvp_improvement, reverse_migrate_mvp_improvement),
    ]
