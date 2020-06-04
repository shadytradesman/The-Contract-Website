# Generated by Django 2.2.12 on 2020-05-29 23:56

import cells.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0004_auto_20200529_2006'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cell',
            name='invite_link_active',
        ),
        migrations.AlterField(
            model_name='cell',
            name='invite_link_secret_key',
            field=models.CharField(default=cells.models.random_string, max_length=64),
        ),
    ]
