# Generated by Django 3.2.9 on 2022-07-09 14:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0070_alter_stockbattlescar_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='grants_non_stock_element',
            field=models.CharField(blank=True, choices=[('Condition', 'Condition'), ('Circumstance', 'Circumstance'), ('Trophy', 'Trophy'), ('Trauma', 'Trauma'), ('Battle Scar', 'Battle Scar')], max_length=55),
        ),
        migrations.AddField(
            model_name='liability',
            name='grants_non_stock_element',
            field=models.CharField(blank=True, choices=[('Condition', 'Condition'), ('Circumstance', 'Circumstance'), ('Trophy', 'Trophy'), ('Trauma', 'Trauma'), ('Battle Scar', 'Battle Scar')], max_length=55),
        ),
        migrations.AlterField(
            model_name='asset',
            name='grants_element',
            field=models.ForeignKey(blank=True, help_text='Grants stock element', null=True, on_delete=django.db.models.deletion.CASCADE, to='characters.stockworldelement'),
        ),
        migrations.AlterField(
            model_name='asset',
            name='grants_scar',
            field=models.ForeignKey(blank=True, help_text='Grants stock scar', null=True, on_delete=django.db.models.deletion.CASCADE, to='characters.stockbattlescar'),
        ),
        migrations.AlterField(
            model_name='liability',
            name='grants_element',
            field=models.ForeignKey(blank=True, help_text='Grants stock element', null=True, on_delete=django.db.models.deletion.CASCADE, to='characters.stockworldelement'),
        ),
        migrations.AlterField(
            model_name='liability',
            name='grants_scar',
            field=models.ForeignKey(blank=True, help_text='Grants stock scar', null=True, on_delete=django.db.models.deletion.CASCADE, to='characters.stockbattlescar'),
        ),
    ]
