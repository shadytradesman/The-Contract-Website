# Generated by Django 2.2.13 on 2021-04-15 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0029_auto_20210415_1927'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roll',
            name='speed',
            field=models.CharField(choices=[('NA', 'not applicable'), ('FREE', 'a Free Action'), ('ACTION_QUICK', 'a Quick Action'), ('ACTION_SPLITTABLE', 'an Action that may be split'), ('ACTION_COMMITTED', 'a Committed Action'), ('REACTION', 'a Reaction')], default='NA', max_length=30),
        ),
    ]
