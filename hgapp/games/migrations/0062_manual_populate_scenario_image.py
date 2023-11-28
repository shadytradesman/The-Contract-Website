from django.db import migrations, models
from django.db import transaction
from django.utils import timezone

def migrate_exchange_reward_increase(apps, schema_editor):
    Scenario = apps.get_model('games', 'Scenario')

def reverse_migrate_exchange_reward_increase():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0061_manual_exchange_reward_increase'),
    ]

    operations = [
        migrations.RunPython(migrate_exchange_reward_increase, reverse_migrate_exchange_reward_increase),
    ]
