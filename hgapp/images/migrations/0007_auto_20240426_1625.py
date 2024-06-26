# Generated by Django 3.2.20 on 2024-04-26 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('images', '0006_privateuserimage_is_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='privateuserimage',
            name='image_height',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='privateuserimage',
            name='image_width',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='privateuserimage',
            name='thumbnail_height',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='privateuserimage',
            name='thumbnail_width',
            field=models.IntegerField(null=True),
        ),
    ]
