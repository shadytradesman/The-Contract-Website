from django.db import migrations

from characters.models import HIGH_ROLLER_STATUS

def reverse_migrate_update_stats(apps, schema_editor):
    pass

def migrate_update_stats(apps, schema_editor):
    Character = apps.get_model('characters', 'Character')
    for character in Character.objects.all():
        character.num_games = character.game_attendance_set.exclude(outcome=None, is_confirmed=False).count()
        character.num_victories = character.game_attendance_set.filter(is_confirmed=True, outcome="WIN").count()
        character.num_losses = character.game_attendance_set.filter(is_confirmed=True, outcome="LOSS").count()
        if character.num_victories == 0 and character.num_losses == 0:
            character.status =  HIGH_ROLLER_STATUS[1][0]
        elif character.num_victories < 10:
            character.status = HIGH_ROLLER_STATUS[2][0]
        elif character.num_victories < 30:
            character.status = HIGH_ROLLER_STATUS[3][0]
        else:
            character.status = HIGH_ROLLER_STATUS[4][0]
        character.save()


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0042_auto_20210905_0352'),
    ]

    operations = [
        migrations.RunPython(migrate_update_stats, reverse_migrate_update_stats),
    ]

