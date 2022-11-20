from django.db import migrations, models
from django.db import transaction


def migrate_create_primary_writeup(apps, schema_editor):
    Scenario = apps.get_model('games', 'Scenario')
    ScenarioWriteup = apps.get_model('games', 'ScenarioWriteup')
    for scenario in Scenario.objects.all():
        with transaction.atomic():
            ScenarioWriteup.objects.create(writer=scenario.creator,
                                           summary=scenario.summary,
                                           section_mission=scenario.description,
                                           suggested_status=scenario.suggested_status,
                                           max_players=scenario.max_players,
                                           min_players=scenario.min_players,
                                           is_highlander=scenario.is_highlander,
                                           requires_ringer=scenario.requires_ringer,
                                           is_rivalry=scenario.is_rivalry,
                                           relevant_scenario=scenario,
                                           num_words=scenario.num_words)


def reverse_migrate_primary_writeup():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0048_auto_20221120_1635'),
    ]

    operations = [
        migrations.RunPython(migrate_create_primary_writeup, reverse_migrate_primary_writeup),
    ]
