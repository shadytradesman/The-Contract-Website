# Generated by Django 3.2.15 on 2023-03-25 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0095_quirk_value_multiply'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcerevision',
            name='refill_condition',
            field=models.CharField(max_length=10000, null=True),
        ),
    ]
