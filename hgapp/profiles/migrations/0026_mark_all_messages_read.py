from django.db import migrations, models
from django.utils.timezone import now

def migrate_scenario_spoiler(apps, schema_editor):
    Message = apps.get_model('postman', 'Message')
    for message in Message.objects.filter(read_at__isnull=True).all():
        message.read_at = now()
        message.save()


def reverse_migrate_primary_writeup():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0025_profile_is_private'),
    ]

    operations = [
        migrations.RunPython(migrate_scenario_spoiler, reverse_migrate_primary_writeup),
    ]
