# Generated by Django 3.2.15 on 2022-12-18 15:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0053_alter_scenarioelement_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario_discovery',
            name='is_aftermath_spoiled',
            field=models.BooleanField(default=True),
        ),
    ]
