# Generated by Django 3.2.9 on 2021-12-18 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0009_webhook'),
    ]

    operations = [
        migrations.AddField(
            model_name='webhook',
            name='mention_group_id',
            field=models.BigIntegerField(blank=True, help_text="Optional. The Discord group ID to @mention when this webhook posts. Find by typing '\\@GROUPNAME' in your Discord server and copying the number.", null=True),
        ),
        migrations.AlterField(
            model_name='webhook',
            name='url',
            field=models.CharField(help_text="The Discord webhook's URL", max_length=2000),
        ),
    ]
