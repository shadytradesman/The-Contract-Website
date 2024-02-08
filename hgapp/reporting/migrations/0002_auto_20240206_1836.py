# Generated by Django 3.2.20 on 2024-02-06 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reporting', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='moderation_action',
            field=models.CharField(blank=True, choices=[('OBSCENE', 'Obscene or explicit content'), ('DOX', 'Sharing personal information'), ('HARASSMENT', 'Abuse or harassment'), ('ADVERTISING', 'Unsolicited advertising or sales'), ('SPAM', 'Spam'), ('OTHER', 'Other (specify below)')], max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='moderation_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='report',
            name='moderator_feedback',
            field=models.TextField(blank=True, max_length=6000, null=True),
        ),
    ]
