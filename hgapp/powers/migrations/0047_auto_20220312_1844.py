# Generated by Django 3.2.9 on 2022-03-12 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0046_auto_20220309_1800'),
    ]

    operations = [
        migrations.AddField(
            model_name='base_power',
            name='icon',
            field=models.FileField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='drawback',
            name='category',
            field=models.CharField(choices=[('MOD_GIFT', 'Gift Type'), ('MOD_ACTIVATION', 'Activation / Targeting'), ('MOD_EFFECT', 'Effect')], default='MOD_EFFECT', help_text='For filtering on create gift page', max_length=30),
        ),
        migrations.AlterField(
            model_name='enhancement',
            name='category',
            field=models.CharField(choices=[('MOD_GIFT', 'Gift Type'), ('MOD_ACTIVATION', 'Activation / Targeting'), ('MOD_EFFECT', 'Effect')], default='MOD_EFFECT', help_text='For filtering on create gift page', max_length=30),
        ),
    ]
