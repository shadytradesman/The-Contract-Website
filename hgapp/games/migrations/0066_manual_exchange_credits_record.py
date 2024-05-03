from django.db import migrations, models
from django.utils.timezone import now

def migrate_credits_record(apps, schema_editor):
    Profile = apps.get_model('profiles', 'Profile')
    ExchangeCreditChange = apps.get_model('games', 'ExchangeCreditChange')
    for profile in Profile.objects.all():
        ExchangeCreditChange.objects.create(rewarded_player=profile.user,
                                            reason="Pre-existing Exchange Credits",
                                            value=profile.exchange_credits)


def reverse_migrate_primary_writeup():
    pass


class Migration(migrations.Migration):

    dependencies = [
         ('games', '0065_exchangecreditchange'),
    ]

    operations = [
        migrations.RunPython(migrate_credits_record, reverse_migrate_primary_writeup),
    ]
