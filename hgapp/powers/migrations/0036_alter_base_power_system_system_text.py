# Generated by Django 3.2.9 on 2022-01-14 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0035_alter_base_power_system_system_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='base_power_system',
            name='system_text',
            field=models.TextField(help_text="((marker1,marker2)) : join markers with 'and'.<br>@@marker1,marker2%% : join markers with 'or'.<br>((marker))^ or @@marker%%^ : join as list and capitalize first character. <br>[[marker|default]] : replace marker, or use default if no replacement.<br>[[marker]] : replace marker or blank if no replacement.<br>{{marker}} : replace marker, paragraph breaks between multiple entries."),
        ),
    ]
