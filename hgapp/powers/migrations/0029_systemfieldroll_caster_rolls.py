# Generated by Django 2.2.13 on 2021-08-02 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0028_auto_20210530_0137'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemfieldroll',
            name='caster_rolls',
            field=models.BooleanField(default=True),
        ),
    ]
