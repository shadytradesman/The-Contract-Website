# Generated by Django 2.2.13 on 2021-03-03 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0021_systemfieldroll_systemfieldrollinstance_systemfieldtext_systemfieldtextinstance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drawback_instance',
            name='detail',
            field=models.CharField(blank=True, max_length=1500, null=True),
        ),
        migrations.AlterField(
            model_name='enhancement_instance',
            name='detail',
            field=models.CharField(blank=True, max_length=1500, null=True),
        ),
    ]