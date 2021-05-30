# Generated by Django 2.2.13 on 2021-05-22 14:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0008_auto_20210521_0240'),
        ('characters', '0034_auto_20210521_0240'),
    ]

    operations = [
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(max_length=1000)),
                ('system', models.CharField(max_length=1000)),
                ('cell', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cells.Cell')),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.Character')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Circumstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(max_length=1000)),
                ('system', models.CharField(max_length=1000)),
                ('cell', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cells.Cell')),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.Character')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Artifact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(max_length=1000)),
                ('system', models.CharField(max_length=1000)),
                ('cell', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='cells.Cell')),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.Character')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
