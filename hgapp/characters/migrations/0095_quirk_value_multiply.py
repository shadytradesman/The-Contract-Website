# Generated by Django 3.2.15 on 2022-10-05 13:57

from django.db import migrations

def migrate_quirk_multiply(apps, schema_editor):
    Asset = apps.get_model('characters', 'Asset')
    Liability = apps.get_model('characters', 'Liability')
    for asset in Asset.objects.all():
        asset.value = asset.value * 3
        asset.save()
    for liability in Liability.objects.all():
        liability.value = liability.value * 3
        liability.save()


def reverse_migrate_denormralize_death(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0094_character_started_supernatural'),
    ]

    operations = [
        migrations.RunPython(migrate_quirk_multiply, reverse_migrate_denormralize_death),
    ]
