# Generated by Django 3.2.20 on 2024-04-26 16:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0005_manual_image_dimensions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fakead',
            name='picture_height',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='fakead',
            name='picture_width',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
