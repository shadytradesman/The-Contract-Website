from django.db import migrations, models
from django.db import transaction
from django.conf import settings

def migrate_email_prefs(apps, schema_editor):
    Profile = apps.get_model('profiles', 'Profile')
    for profile in Profile.objects.all():
        if not profile.contract_invitations or not profile.contract_updates:
            print("updating {}".format(profile.user.username))
            for membership in profile.user.cellmembership_set.all():
                membership.email_contract_updates = profile.contract_updates
                membership.email_contract_invites = profile.contract_invitations
                membership.save()

def reverse_mig(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0017_auto_20240710_0037'),
    ]

    operations = [
        migrations.RunPython(migrate_email_prefs, reverse_mig),
    ]
