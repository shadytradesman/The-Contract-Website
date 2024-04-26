from django.db import migrations, models
from django.db import transaction
from django.conf import settings

def migrate_image_dimensions(apps, schema_editor):
    PrivateUserImage = apps.get_model('images', 'PrivateUserImage')
    for image in PrivateUserImage.objects.all():
        try:
            image.image_height = image.image.height
            image.image_width = image.image.width
            if hasattr(image, "thumbnail") and image.thumbnail is not None:
                image.thumbnail_height = image.thumbnail.height
                image.thumbnail_width = image.thumbnail.width
            image.save()
        except:
            print("could not update image {}".format(image.pk))
            image.image_height = 0
            image.image_width = 0
            image.thumbnail_height = 0
            image.thumbnail_width = 0
            image.save()

def reverse_mig(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('images', '0007_auto_20240426_1625'),
    ]

    operations = [
        migrations.RunPython(migrate_image_dimensions, reverse_mig),
    ]
