# Generated by Django 3.2.15 on 2023-06-11 18:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0098_man_recalculate_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='sourcerevision',
            name='refill_condition_professional',
            field=models.CharField(max_length=10000, null=True),
        ),
        migrations.AddField(
            model_name='sourcerevision',
            name='refill_condition_veteran',
            field=models.CharField(max_length=10000, null=True),
        ),
    ]
