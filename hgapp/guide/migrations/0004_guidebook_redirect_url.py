# Generated by Django 2.2.13 on 2021-10-01 22:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('guide', '0003_auto_20211001_2225'),
    ]

    operations = [
        migrations.AddField(
            model_name='guidebook',
            name='redirect_url',
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]
