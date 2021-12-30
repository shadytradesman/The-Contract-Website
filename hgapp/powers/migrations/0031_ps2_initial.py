from django.db import migrations
from django.db import transaction


def port_modifiers_to_v2(base):
    base.avail_enhancements.add(*base.enhancements.all())
    base.avail_drawbacks.add(*base.drawbacks.all())
    base.save()

def migrate_initial_ps2(apps, schema_editor):
    Base_Power = apps.get_model('powers', 'Base_Power')
    for base in Base_Power.objects.all():
        with transaction.atomic():
            port_modifiers_to_v2(base)

def reverse_migrate_initial_ps2(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0030_auto_20211230_1829'),
    ]

    operations = [
        migrations.RunPython(migrate_initial_ps2, reverse_migrate_initial_ps2),
    ]
