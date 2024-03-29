# Generated by Django 3.2.15 on 2022-12-06 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0051_auto_20221206_1422'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenarioelement',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='scenarioelement',
            name='type',
            field=models.CharField(choices=[('Condition', 'Condition'), ('Circumstance', 'Circumstance'), ('Trophy', 'Trophy'), ('Trauma', 'Trauma'), ('Loose End', 'Loose End')], default='Condition', max_length=45),
        ),
    ]
