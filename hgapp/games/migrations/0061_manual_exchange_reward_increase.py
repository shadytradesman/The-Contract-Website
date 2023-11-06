from django.db import migrations, models
from django.db import transaction
from django.utils import timezone

def migrate_exchange_reward_increase(apps, schema_editor):
    Scenario = apps.get_model('games', 'Scenario')
    for scenario in Scenario.objects.all():
        if scenario.is_on_exchange:
            scenario.creator.profile.exchange_credits = scenario.creator.profile.exchange_credits + 100
            scenario.creator.profile.save()

def reverse_migrate_exchange_reward_increase():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0060_reward_is_questionnaire'),
    ]

    operations = [
        migrations.RunPython(migrate_exchange_reward_increase, reverse_migrate_exchange_reward_increase),
    ]
