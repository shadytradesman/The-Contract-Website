# Generated by Django 3.2.15 on 2022-10-05 13:57

from django.db import migrations

STATUS_ANY = 'ANY'
STATUS_NEWBIE = 'NEWBIE'
STATUS_NOVICE = 'NOVICE'
STATUS_SEASONED = 'SEASONED'
STATUS_PROFESSIONAL = 'PROFESSIONAL'
STATUS_VETERAN = 'VETERAN'

def recalculate_status(character):
    num_victories = character.num_victories if character.num_victories else 0
    if num_victories < 4:
        return STATUS_NEWBIE
    elif num_victories < 10:
        return STATUS_NOVICE
    elif num_victories < 17:
        return STATUS_SEASONED
    elif num_victories < 25:
        return STATUS_PROFESSIONAL
    else:
        return STATUS_VETERAN


def migrate_redo_status(apps, schema_editor):
    Character = apps.get_model('characters', 'Character')
    for character in Character.objects.all():
        character.status = recalculate_status(character)
        character.save()


def reverse_migrate_denormralize_death(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0097_alter_character_status'),
    ]

    operations = [
        migrations.RunPython(migrate_redo_status, reverse_migrate_denormralize_death),
    ]
