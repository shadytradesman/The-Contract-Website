# Generated by Django 3.2.9 on 2022-03-27 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0064_auto_20220326_1840'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artifact',
            name='location',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
    ]
