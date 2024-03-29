# Generated by Django 2.2.13 on 2021-09-05 18:40

from django.db import migrations, models

def reverse_migrate_update_stats(apps, schema_editor):
    pass

def migrate_update_stats(apps, schema_editor):
    Character = apps.get_model('characters', 'Character')
    for character in Character.objects.all():
        character.num_journals = character.game_attendance_set \
            .filter(relevant_game__end_time__isnull=False, journal__isnull=False, journal__is_valid=True) \
            .count()
        character.save()

class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0045_auto_20210905_1840'),
    ]

    operations = [
        migrations.RunPython(migrate_update_stats, reverse_migrate_update_stats),
    ]
