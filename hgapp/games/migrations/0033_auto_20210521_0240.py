# Generated by Django 2.2.13 on 2021-05-21 02:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0032_game_allow_ringers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='game',
            name='invitation_mode',
            field=models.CharField(choices=[('INVITE_ONLY', 'Invited Players Only'), ('WORLD_MEMBERS', 'World Members Only'), ('ANYONE', 'Any Player'), ('CLOSED', 'Closed for RSVPs')], default='INVITE_ONLY', max_length=25),
        ),
    ]