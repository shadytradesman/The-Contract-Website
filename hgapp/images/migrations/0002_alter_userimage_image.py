# Generated by Django 3.2.15 on 2022-11-29 15:22

from django.db import migrations, models
import images.models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userimage',
            name='image',
            field=models.ImageField(upload_to=images.models.image_upload_name),
        ),
    ]