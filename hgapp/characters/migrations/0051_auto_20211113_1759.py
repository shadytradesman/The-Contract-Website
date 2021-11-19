# Generated by Django 2.2.13 on 2021-11-13 17:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0050_auto_20210925_1818'),
    ]

    operations = [
        migrations.AddField(
            model_name='experiencereward',
            name='type',
            field=models.CharField(choices=[('MVP', 'earning MVP'), ('LOSS_V1', 'losing'), ('LOSS_RINGER_V1', 'losing as a ringer'), ('WIN_V1', 'winning'), ('WIN_RINGER_V1', 'winning as a ringer'), ('LOSS_V2', 'losing'), ('LOSS_RINGER_V2', 'losing as a ringer'), ('WIN_V2', 'winning'), ('WIN_RINGER_V2', 'winning as a ringer'), ('IN_WORLD', 'playing in-World'), ('GM', 'GMing'), ('JOURNAL', 'writing a journal'), ('CUSTOM', 'custom reason')], default='MVP', max_length=45),
        ),
        migrations.AddIndex(
            model_name='experiencereward',
            index=models.Index(fields=['rewarded_character', 'created_time'], name='characters__rewarde_3a375d_idx'),
        ),
        migrations.AddIndex(
            model_name='experiencereward',
            index=models.Index(fields=['rewarded_character', 'is_void', 'type'], name='characters__rewarde_d66313_idx'),
        ),
        migrations.AddIndex(
            model_name='experiencereward',
            index=models.Index(fields=['rewarded_player', 'rewarded_character'], name='characters__rewarde_4604ad_idx'),
        ),
    ]
