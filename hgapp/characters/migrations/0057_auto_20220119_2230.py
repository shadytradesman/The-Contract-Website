# Generated by Django 3.2.9 on 2022-01-19 22:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0056_alter_character_tagline'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockBattleScar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('1MINOR', 'Minor Scars'), ('2MAJOR', 'Major Scars'), ('3SEVERE', 'Severe Scars'), ('4EXTREME', 'Extreme Scars')], default='1MINOR', max_length=45)),
                ('description', models.CharField(max_length=500)),
                ('system', models.CharField(max_length=500)),
            ],
        ),
        migrations.AddField(
            model_name='battlescar',
            name='system',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
