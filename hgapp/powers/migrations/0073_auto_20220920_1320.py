# Generated by Django 3.2.15 on 2022-09-20 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0072_powersystem_cache_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='drawback_instance',
            name='is_advancement',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='enhancement_instance',
            name='is_advancement',
            field=models.BooleanField(default=False),
        ),
    ]