from django.db import migrations, models
from django.db import transaction
from django.conf import settings

def migrate_image_dimensions(apps, schema_editor):
    PrivateUserImage = apps.get_model('images', 'PrivateUserImage')
    for image in PrivateUserImage.objects.filter(image_height=0).order_by("id"):
        try:
            image.image_height = image.image.height
            image.image_width = image.image.width
            image.save()
            print("updated image {}".format(image.pk))
        except:
            print("could not update image {}".format(image.pk))
            image.image_height = 0
            image.image_width = 0
            image.save()

def reverse_mig(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('images', '0010_auto_20240426_1716'),
    ]

    operations = [
        migrations.RunPython(migrate_image_dimensions, reverse_mig),
    ]
