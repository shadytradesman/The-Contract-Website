# Generated by Django 3.2.9 on 2022-03-12 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0047_auto_20220312_1844'),
    ]

    operations = [
        migrations.AddField(
            model_name='base_power_category',
            name='color',
            field=models.CharField(default='#111418', max_length=8),
        ),
        migrations.AlterField(
            model_name='drawback',
            name='category',
            field=models.CharField(choices=[('MOD_ACTIVATION', 'Activation / Targeting'), ('MOD_EFFECT', 'Effect'), ('MOD_GIFT', 'Gift Type')], default='MOD_EFFECT', help_text='For filtering on create gift page', max_length=30),
        ),
        migrations.AlterField(
            model_name='enhancement',
            name='category',
            field=models.CharField(choices=[('MOD_ACTIVATION', 'Activation / Targeting'), ('MOD_EFFECT', 'Effect'), ('MOD_GIFT', 'Gift Type')], default='MOD_EFFECT', help_text='For filtering on create gift page', max_length=30),
        ),
    ]
