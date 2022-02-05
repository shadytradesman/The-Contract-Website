# Generated by Django 3.2.9 on 2022-02-05 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0059_alter_weapon_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='weapon',
            name='attack_system_text',
            field=models.CharField(blank=True, help_text='If no actual roll is specified, use this in power system text', max_length=300),
        ),
    ]
