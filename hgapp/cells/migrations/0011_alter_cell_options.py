# Generated by Django 3.2.9 on 2022-01-17 20:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0010_auto_20211218_1744'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cell',
            options={'permissions': (('admin', 'Administrate'), ('manage_memberships', 'Manage Memberships'), ('manage_roles', 'Run Games'), ('post_events', 'Post World Events'), ('manage_member_characters', 'Manage Contractors'), ('edit_world', 'Edit Playgroup'), ('manage_games', 'Manage Games'))},
        ),
    ]
