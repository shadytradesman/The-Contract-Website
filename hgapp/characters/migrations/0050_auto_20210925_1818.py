# Generated by Django 2.2.13 on 2021-09-25 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0049_character_ported'),
    ]

    operations = [
        migrations.AlterField(
            model_name='character',
            name='ported',
            field=models.CharField(choices=[('NOT_PORTED', 'Not ported'), ('SEASONED_PORTED', 'Ported as Seasoned'), ('VETERAN_PORTED', 'Ported as Veteran')], default='NOT_PORTED', max_length=50),
        ),
    ]
