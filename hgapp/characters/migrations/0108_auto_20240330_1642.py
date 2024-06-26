# Generated by Django 3.2.20 on 2024-03-30 16:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0107_man_character_earned_exp'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArtifactTimelineEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('notes', models.CharField(blank=True, max_length=5000)),
                ('relevant_artifact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='characters.artifact')),
            ],
        ),
        migrations.AddIndex(
            model_name='artifacttimelineevent',
            index=models.Index(fields=['relevant_artifact', 'created_time'], name='characters__relevan_f77050_idx'),
        ),
    ]
