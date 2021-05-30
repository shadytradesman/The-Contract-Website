# Generated by Django 2.2.13 on 2021-05-16 15:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0006_cell_find_world_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='cell',
            name='game_death',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cell',
            name='game_loss',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cell',
            name='game_victory',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
