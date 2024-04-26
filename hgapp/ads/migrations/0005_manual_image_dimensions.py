from django.db import migrations, models
from django.db import transaction
from django.conf import settings

def migrate_image_dimensions(apps, schema_editor):
    FakeAd = apps.get_model('ads', 'FakeAd')
    for image in FakeAd.objects.all():
        try:
            image.picture_height = image.picture.height
            image.picture_width = image.picture.width
            image.save()
        except:
            print("could not update image {}".format(image.pk))
            image.picture_height = 0
            image.picture_width = 0
            image.save()


def reverse_mig(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0004_auto_20240426_1625'),
    ]

    operations = [
        migrations.RunPython(migrate_image_dimensions, reverse_mig),
    ]
