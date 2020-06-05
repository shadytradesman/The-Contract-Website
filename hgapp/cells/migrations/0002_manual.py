import cells.models
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cell',
            name='invite_link_secret_key',
            field=models.CharField(default=cells.models.random_string, max_length=64),
        ),
        migrations.AddField(
            model_name='cellinvite',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now,
                                       verbose_name='date created'),
            preserve_default=False,
        ),
    ]