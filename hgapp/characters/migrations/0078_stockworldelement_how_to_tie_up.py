# Generated by Django 3.2.9 on 2022-07-25 14:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0077_auto_20220725_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockworldelement',
            name='how_to_tie_up',
            field=models.CharField(blank=True, help_text='For Loose Ends only', max_length=1000),
        ),
    ]
