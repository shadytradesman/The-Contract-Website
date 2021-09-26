# Generated by Django 2.2.13 on 2021-09-09 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0046_journal_stats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='character',
            name='num_games',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='character',
            name='num_journals',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='character',
            name='num_losses',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='character',
            name='num_victories',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
