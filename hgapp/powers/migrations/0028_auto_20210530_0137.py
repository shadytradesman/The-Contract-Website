# Generated by Django 2.2.13 on 2021-05-30 01:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0036_auto_20210530_0137'),
        ('powers', '0027_base_power_system_default_description_prompt'),
    ]

    operations = [
        migrations.AddField(
            model_name='parameter',
            name='attribute_bonus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='characters.Attribute'),
        ),
        migrations.AddField(
            model_name='power_full',
            name='latest_rev',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='powers.Power'),
        ),
    ]
