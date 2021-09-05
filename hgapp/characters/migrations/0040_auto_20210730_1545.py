# Generated by Django 2.2.13 on 2021-07-30 15:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0039_charactertutorial_wound'),
    ]

    operations = [
        migrations.AddField(
            model_name='charactertutorial',
            name='dodge_roll',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='char_dodge', to='characters.Roll'),
        ),
        migrations.AddField(
            model_name='charactertutorial',
            name='sprint_roll',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='char_sprint', to='characters.Roll'),
        ),
    ]
