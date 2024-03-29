# Generated by Django 3.2.9 on 2022-02-26 19:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0063_alter_stockbattlescar_type'),
        ('powers', '0042_auto_20220213_1822'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArtifactPower',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('detail', models.CharField(blank=True, max_length=1500, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='powerhistory',
            name='latest_rev',
        ),
        migrations.RemoveField(
            model_name='powerhistory',
            name='parent_power',
        ),
        migrations.RemoveField(
            model_name='power',
            name='power_history',
        ),
        migrations.AddField(
            model_name='power',
            name='errata',
            field=models.TextField(blank=True, default='', max_length=54000),
        ),
        migrations.AlterField(
            model_name='drawback',
            name='category',
            field=models.CharField(choices=[('MOD_EFFECT', 'Effect'), ('MOD_GIFT', 'Gift Type'), ('MOD_ACTIVATION', 'Activation / Targeting')], default='MOD_EFFECT', help_text='For filtering on create gift page', max_length=30),
        ),
        migrations.AlterField(
            model_name='enhancement',
            name='category',
            field=models.CharField(choices=[('MOD_EFFECT', 'Effect'), ('MOD_GIFT', 'Gift Type'), ('MOD_ACTIVATION', 'Activation / Targeting')], default='MOD_EFFECT', help_text='For filtering on create gift page', max_length=30),
        ),
        migrations.AlterField(
            model_name='power',
            name='system',
            field=models.TextField(blank=True, max_length=54000, null=True),
        ),
        migrations.AddIndex(
            model_name='power',
            index=models.Index(fields=['parent_power', 'pub_date'], name='powers_powe_parent__405689_idx'),
        ),
        migrations.AddIndex(
            model_name='power_full',
            index=models.Index(fields=['owner', 'is_deleted', 'dice_system'], name='powers_powe_owner_i_9d5a7e_idx'),
        ),
        migrations.AddIndex(
            model_name='power_full',
            index=models.Index(fields=['character', 'dice_system'], name='powers_powe_charact_0afe32_idx'),
        ),
        migrations.DeleteModel(
            name='PowerHistory',
        ),
        migrations.AddField(
            model_name='artifactpower',
            name='relevant_artifact',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='characters.artifact'),
        ),
        migrations.AddField(
            model_name='artifactpower',
            name='relevant_power',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='powers.power'),
        ),
        migrations.AddField(
            model_name='power',
            name='artifacts',
            field=models.ManyToManyField(through='powers.ArtifactPower', to='characters.Artifact'),
        ),
    ]
