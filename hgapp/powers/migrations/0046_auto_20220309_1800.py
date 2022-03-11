# Generated by Django 3.2.9 on 2022-03-09 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0045_auto_20220309_0305'),
    ]

    operations = [
        migrations.AddField(
            model_name='power',
            name='gift_cost',
            field=models.IntegerField(null=True),
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
