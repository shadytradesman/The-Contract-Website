# Generated by Django 3.2.20 on 2024-04-26 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0003_fakead_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='fakead',
            name='picture_height',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='fakead',
            name='picture_width',
            field=models.IntegerField(null=True),
        ),
    ]
