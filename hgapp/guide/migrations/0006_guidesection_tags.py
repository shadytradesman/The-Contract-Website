# Generated by Django 3.2.9 on 2021-12-18 02:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guide', '0005_guidesection_is_hidden'),
    ]

    operations = [
        migrations.AddField(
            model_name='guidesection',
            name='tags',
            field=models.JSONField(default=list),
        ),
    ]