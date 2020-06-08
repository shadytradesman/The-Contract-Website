# Generated by Django 2.2.12 on 2020-06-08 15:39

from django.db import migrations, models

from games.models import migrate_add_gms, reverse_add_gms_migration
from django.conf import settings
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('games', '0011_auto_20200605_0541'),
    ]

    operations = [
        migrations.AddField(
            model_name='game_attendance',
            name='is_confirmed',
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(migrate_add_gms, reverse_add_gms_migration),
        migrations.AlterField(
            model_name='game',
            name='gm',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,
                                    related_name='game_gm', to=settings.AUTH_USER_MODEL),
        ),
    ]
