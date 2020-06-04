# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-12-12 03:30
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0012_graveyard_header'),
        ('powers', '0010_auto_20170711_0329'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('games', '0005_merge_20170914_0552'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reward',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_improvement', models.BooleanField(default=True)),
                ('is_void', models.BooleanField(default=False)),
                ('awarded_on', models.DateTimeField(verbose_name='awarded on')),
                ('assigned_on', models.DateTimeField(blank=True, null=True, verbose_name='assigned on')),
                ('relevant_game', models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='games.Game')),
                ('relevant_power', models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='powers.Power')),
                ('rewarded_character', models.ForeignKey(blank=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='characters.Character')),
                ('rewarded_player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rewarded_player', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='reward',
            unique_together=set([('rewarded_player', 'relevant_game')]),
        ),
    ]
