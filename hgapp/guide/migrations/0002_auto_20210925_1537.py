# Generated by Django 2.2.13 on 2021-09-25 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guide', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='guidesection',
            name='header_level',
            field=models.PositiveIntegerField(default=2),
        ),
    ]
