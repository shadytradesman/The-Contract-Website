# Generated by Django 3.2.15 on 2023-09-23 18:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0060_reward_is_questionnaire'),
        ('questionnaire', '0002_auto_20230923_1557'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='game_attendance',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='games.game_attendance'),
        ),
    ]
