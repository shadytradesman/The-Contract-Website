# Generated by Django 2.2.13 on 2021-02-04 17:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_images', '0001_initial'),
        ('blog', '0020_auto_20171106_2252'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostImageSet',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('pinax_images.imageset',),
        ),
    ]
