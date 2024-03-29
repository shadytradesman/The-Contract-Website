# Generated by Django 3.2.15 on 2022-11-23 16:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('games', '0047_reward_is_gm_reward'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='date created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='scenario',
            name='is_wiki_editable',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='description',
            field=models.TextField(blank=True, max_length=74000),
        ),
        migrations.CreateModel(
            name='ScenarioWriteup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(choices=[('OVERVIEW', 'Overview'), ('BACKSTORY', 'Backstory'), ('INTRODUCTION', 'Intro and Briefing'), ('MISSION', 'Mission'), ('AFTERMATH', 'Aftermath')], default='MISSION', max_length=55)),
                ('content', models.TextField(max_length=74000)),
                ('created_date', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('num_words', models.IntegerField(default=0, verbose_name='Number of Words')),
                ('is_deleted', models.BooleanField(default=False)),
                ('relevant_scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='games.scenario')),
                ('writer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='scenario_writer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='scenariowriteup',
            index=models.Index(fields=['relevant_scenario', 'section', 'is_deleted', 'created_date'], name='games_scena_relevan_265485_idx'),
        ),
        migrations.AddIndex(
            model_name='scenariowriteup',
            index=models.Index(fields=['relevant_scenario', 'section', 'created_date'], name='games_scena_relevan_1b40a3_idx'),
        ),
        migrations.AddIndex(
            model_name='scenariowriteup',
            index=models.Index(fields=['relevant_scenario', 'created_date'], name='games_scena_relevan_89a37a_idx'),
        ),
        migrations.AddIndex(
            model_name='scenariowriteup',
            index=models.Index(fields=['writer'], name='games_scena_writer__39c741_idx'),
        ),
    ]
