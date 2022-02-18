# Generated by Django 3.2.9 on 2022-02-05 19:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0038_auto_20220201_0436'),
    ]

    operations = [
        migrations.AlterField(
            model_name='base_power',
            name='vector_cost_credit',
            field=models.ManyToManyField(help_text='SET ON EFFECTS ONLY. Any Gift using this Effect and the listed Vector will be reduced in cost by the credit.', through='powers.VectorCostCredit', to='powers.Base_Power'),
        ),
        migrations.AlterField(
            model_name='vectorcostcredit',
            name='gift_credit',
            field=models.IntegerField(help_text='The cost of any Gift using this combination of Effect and Vector is reduced by this amount.', verbose_name='Gift Credit'),
        ),
    ]