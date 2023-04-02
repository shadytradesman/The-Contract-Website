from django.db import migrations, models
from django.db import transaction
from django.conf import settings


def migrate_scenario_spoiler(apps, schema_editor):
    ScenarioTag = apps.get_model('games', 'ScenarioTag')
    User = apps.get_model('auth', "User")
    ScenarioDiscovery = apps.get_model('games', 'Scenario_Discovery')
    scenarios = []
    for tag in ScenarioTag.objects.filter(tag="public"):
        scenarios = tag.scenario_set.all()
    for user in User.objects.all():
        for scenario in scenarios:
            with transaction.atomic():
                unlocked_discovery(scenario, user, ScenarioDiscovery)


def unlocked_discovery(scenario, player, Scenario_Discovery):
    if not player.scenario_set.filter(id=scenario.id).exists():
        discovery = Scenario_Discovery(
            discovering_player=player,
            relevant_scenario=scenario,
            reason="UNLOCKED",
            is_spoiled=False,
        )
        discovery.save()


def reverse_migrate_primary_writeup():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0054_scenario_discovery_is_aftermath_spoiled'),
    ]

    operations = [
        migrations.RunPython(migrate_scenario_spoiler, reverse_migrate_primary_writeup),
    ]
