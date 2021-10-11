# Generated by Django 2.2.13 on 2021-10-11 18:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0050_auto_20210925_1818'),
        ('info', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuickStartInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('main_char', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.Character')),
            ],
        ),
        migrations.CreateModel(
            name='ExampleAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=3000)),
                ('is_contested', models.BooleanField(default=False)),
                ('is_secondary', models.BooleanField(default=False)),
                ('is_first_roll', models.BooleanField(default=False)),
                ('additional_rules_info', models.TextField(default='', max_length=3000)),
                ('outcome_botch', models.TextField(max_length=3000)),
                ('outcome_botch_extra', models.TextField(blank=True, max_length=3000, null=True)),
                ('outcome_failure', models.TextField(max_length=3000)),
                ('outcome_failure_extra', models.TextField(blank=True, max_length=3000, null=True)),
                ('outcome_partial_success', models.TextField(max_length=3000)),
                ('outcome_partial_success_extra', models.TextField(blank=True, max_length=3000, null=True)),
                ('outcome_complete_success', models.TextField(max_length=3000)),
                ('outcome_complete_success_extra', models.TextField(blank=True, max_length=3000, null=True)),
                ('outcome_exceptional_success', models.TextField(max_length=3000)),
                ('outcome_exceptional_success_extra', models.TextField(blank=True, max_length=3000, null=True)),
                ('roll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.Roll')),
            ],
        ),
    ]
