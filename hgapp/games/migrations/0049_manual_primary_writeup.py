from django.db import migrations, models
from django.db import transaction


MISSION = "MISSION"
def migrate_create_primary_writeup(apps, schema_editor):
    Scenario = apps.get_model('games', 'Scenario')
    ScenarioWriteup = apps.get_model('games', 'ScenarioWriteup')
    for scenario in Scenario.objects.all():
        with transaction.atomic():
            ScenarioWriteup.objects.create(writer=scenario.creator,
                                           section=MISSION,
                                           content=scenario.description,
                                           relevant_scenario=scenario,
                                           num_words=scenario.num_words)

def reverse_migrate_primary_writeup():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0048_auto_20221123_1636'),
    ]

    operations = [
        migrations.RunPython(migrate_create_primary_writeup, reverse_migrate_primary_writeup),
    ]
