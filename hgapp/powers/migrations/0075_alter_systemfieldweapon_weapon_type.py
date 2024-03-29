# Generated by Django 3.2.15 on 2023-01-23 03:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0074_power_full_stock_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='systemfieldweapon',
            name='weapon_type',
            field=models.CharField(blank=True, choices=[('MELEE', 'Melee'), ('UNARMED', 'Unarmed'), ('FIREARM', 'Firearm'), ('THROWN', 'Thrown'), ('THROWN_2', 'Thrown other'), ('PROJECTILE', 'Projectile'), ('OTHER', 'Other')], default='MELEE', help_text='Provides the following substitutions based on the selected weapon: <br>selected-weapon-name, selected-weapon-type, selected-weapon-bonus-damage, selected-weapon-attack-roll, selected-weapon-attack-roll-difficulty, selected-weapon-attack-text, selected-weapon-range, selected-weapon-errata', max_length=30),
        ),
    ]
