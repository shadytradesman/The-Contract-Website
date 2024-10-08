# Generated by Django 3.2.20 on 2024-02-02 16:36

from django.db import migrations, models

CRAFTING_ARTIFACT = 'ARTIFACT_CRAFTING'

def reverse_migrate_earned_exp(apps, schema_editor):
    pass


def migrate_update_earned_exp(apps, schema_editor):
    CraftingEvent = apps.get_model('crafting', 'CraftingEvent')
    for event in CraftingEvent.objects.filter(relevant_power__modality__crafting_type=CRAFTING_ARTIFACT).order_by("pk").all():
        print("examining event ", event.pk)
        power = event.relevant_power
        power_full = event.relevant_power_full
        for art in event.artifacts.all():
            art.power_set.add(power)
            art.power_full_set.add(power_full)
    print("Done")



class Migration(migrations.Migration):

    dependencies = [
        ('crafting', '0003_man_fix_upgrade_refunds'),
    ]

    operations = [
        migrations.RunPython(migrate_update_earned_exp, reverse_migrate_earned_exp),
    ]
