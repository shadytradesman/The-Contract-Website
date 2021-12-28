# Generated by Django 3.2.9 on 2021-12-28 01:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('powers', '0029_systemfieldroll_caster_rolls'),
    ]

    operations = [
        migrations.CreateModel(
            name='FieldSubstitution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('marker', models.SlugField(max_length=300)),
                ('replacement', models.CharField(blank=True, max_length=300)),
                ('mode', models.CharField(choices=[('EPHEMERAL', 'Ephemeral'), ('UNIQUE', 'Unique'), ('ADDITIVE', 'Additive')], default='ADDITIVE', max_length=25)),
            ],
        ),
        migrations.CreateModel(
            name='PowerHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AlterModelOptions(
            name='base_power',
            options={'verbose_name': 'Gift Component'},
        ),
        migrations.AlterModelOptions(
            name='power_full',
            options={'permissions': (('view_private_power_full', 'View private power full'), ('edit_power_full', 'Edit power full')), 'verbose_name': 'Gift'},
        ),
        migrations.RemoveField(
            model_name='base_power',
            name='default_activation_style',
        ),
        migrations.RemoveField(
            model_name='power',
            name='linked_powers',
        ),
        migrations.RemoveField(
            model_name='power_full',
            name='linked_powers',
        ),
        migrations.AddField(
            model_name='base_power',
            name='allowed_modalities',
            field=models.ManyToManyField(blank=True, related_name='vector_modalities', to='powers.Base_Power'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='allowed_vectors',
            field=models.ManyToManyField(blank=True, related_name='vector_effects', to='powers.Base_Power'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='avail_drawbacks',
            field=models.ManyToManyField(blank=True, related_name='avail_drawbacks', to='powers.Drawback', verbose_name='drawbacks'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='avail_enhancements',
            field=models.ManyToManyField(blank=True, related_name='avail_enhancements', to='powers.Enhancement', verbose_name='enhancements'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='base_type',
            field=models.CharField(choices=[('EFFECT', 'Effect'), ('VECTOR', 'Vector'), ('MODALITY', 'Modality')], default='EFFECT', help_text='DO NOT CHANGE THIS AFTER INITIAL CREATION', max_length=25, verbose_name='component type'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='blacklist_drawbacks',
            field=models.ManyToManyField(blank=True, related_name='blacklist_drawbacks', to='powers.Drawback'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='blacklist_enhancements',
            field=models.ManyToManyField(blank=True, related_name='blacklist_enhancements', to='powers.Enhancement'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='blacklist_parameters',
            field=models.ManyToManyField(blank=True, related_name='blacklist_params', to='powers.Parameter'),
        ),
        migrations.AddField(
            model_name='parameter',
            name='default',
            field=models.IntegerField(default=1, help_text='If legacy power system, this field is ignored. 8+ for no retriction', verbose_name='Default Level'),
        ),
        migrations.AddField(
            model_name='parameter',
            name='seasoned_level',
            field=models.IntegerField(default=-1, help_text='If legacy power system, this field is ignored. 8+ for no restriction.', verbose_name='Seasoned Threshold'),
        ),
        migrations.AddField(
            model_name='parameter',
            name='veteran_level',
            field=models.IntegerField(default=-1, help_text='If legacy power system, this field is ignored. 8+ for no restriction', verbose_name='Veteran Threshold'),
        ),
        migrations.AddField(
            model_name='power',
            name='modality',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='power_modality', to='powers.base_power'),
        ),
        migrations.AddField(
            model_name='power',
            name='vector',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='power_vector', to='powers.base_power'),
        ),
        migrations.AddField(
            model_name='power_param',
            name='dice_system',
            field=models.CharField(choices=[('ALL', 'All'), ('HOUSEGAMES15', 'House Games 1.5'), ('PS2', 'New Powers System')], default='HOUSEGAMES15', max_length=55),
        ),
        migrations.AlterField(
            model_name='base_power',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='powers.base_power_category'),
        ),
        migrations.AlterField(
            model_name='base_power',
            name='drawbacks',
            field=models.ManyToManyField(blank=True, to='powers.Drawback', verbose_name='legacy drawbacks'),
        ),
        migrations.AlterField(
            model_name='base_power',
            name='enhancements',
            field=models.ManyToManyField(blank=True, to='powers.Enhancement', verbose_name='legacy enhancements'),
        ),
        migrations.AlterField(
            model_name='base_power',
            name='num_free_enhancements',
            field=models.IntegerField(default=0, verbose_name='gift point credit'),
        ),
        migrations.AlterField(
            model_name='base_power',
            name='required_status',
            field=models.CharField(choices=[('ANY', 'Any'), ('NEWBIE', 'Newbie'), ('NOVICE', 'Novice'), ('SEASONED', 'Seasoned'), ('VETERAN', 'Veteran')], default='ANY', max_length=25),
        ),
        migrations.AlterField(
            model_name='base_power_system',
            name='dice_system',
            field=models.CharField(choices=[('ALL', 'All'), ('HOUSEGAMES15', 'House Games 1.5'), ('PS2', 'New Powers System')], default='PS2', max_length=55),
        ),
        migrations.AlterField(
            model_name='drawback',
            name='required_status',
            field=models.CharField(choices=[('ANY', 'Any'), ('NEWBIE', 'Newbie'), ('NOVICE', 'Novice'), ('SEASONED', 'Seasoned'), ('VETERAN', 'Veteran')], default='ANY', max_length=25),
        ),
        migrations.AlterField(
            model_name='drawback',
            name='system',
            field=models.CharField(choices=[('ALL', 'All'), ('HOUSEGAMES15', 'House Games 1.5'), ('PS2', 'New Powers System')], default='PS2', max_length=55),
        ),
        migrations.AlterField(
            model_name='enhancement',
            name='required_status',
            field=models.CharField(choices=[('ANY', 'Any'), ('NEWBIE', 'Newbie'), ('NOVICE', 'Novice'), ('SEASONED', 'Seasoned'), ('VETERAN', 'Veteran')], default='ANY', max_length=25),
        ),
        migrations.AlterField(
            model_name='enhancement',
            name='system',
            field=models.CharField(choices=[('ALL', 'All'), ('HOUSEGAMES15', 'House Games 1.5'), ('PS2', 'New Powers System')], default='PS2', max_length=55),
        ),
        migrations.AlterField(
            model_name='power',
            name='activation_style',
            field=models.CharField(choices=[('PASSIVE', 'Passive'), ('ACTIVE', 'Active')], default='PASSIVE', max_length=25),
        ),
        migrations.AlterField(
            model_name='power',
            name='base',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='power_effect', to='powers.base_power'),
        ),
        migrations.AlterField(
            model_name='power',
            name='description',
            field=models.TextField(max_length=2500),
        ),
        migrations.AlterField(
            model_name='power',
            name='dice_system',
            field=models.CharField(choices=[('ALL', 'All'), ('HOUSEGAMES15', 'House Games 1.5'), ('PS2', 'New Powers System')], max_length=55),
        ),
        migrations.AlterField(
            model_name='power',
            name='name',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name='power',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date published'),
        ),
        migrations.AlterField(
            model_name='power',
            name='system',
            field=models.TextField(blank=True, max_length=14000, null=True),
        ),
        migrations.AlterField(
            model_name='power_full',
            name='dice_system',
            field=models.CharField(choices=[('ALL', 'All'), ('HOUSEGAMES15', 'House Games 1.5'), ('PS2', 'New Powers System')], max_length=55),
        ),
        migrations.AlterField(
            model_name='power_full',
            name='pub_date',
            field=models.DateTimeField(auto_now_add=True, verbose_name='date published'),
        ),
        migrations.AlterField(
            model_name='power_param',
            name='default',
            field=models.IntegerField(help_text='If v2 power system, this field is ignored.', verbose_name='Default Level'),
        ),
        migrations.AlterField(
            model_name='power_param',
            name='seasoned',
            field=models.IntegerField(help_text='If v2 power system, this field is ignored.', verbose_name='Seasoned Threshold'),
        ),
        migrations.AlterField(
            model_name='power_param',
            name='veteran',
            field=models.IntegerField(help_text='If v2 power system, this field is ignored.', verbose_name='Veteran Threshold'),
        ),
        migrations.AlterUniqueTogether(
            name='power_param',
            unique_together={('relevant_parameter', 'relevant_base_power', 'dice_system')},
        ),
        migrations.DeleteModel(
            name='Power_Link',
        ),
        migrations.AddField(
            model_name='powerhistory',
            name='latest_rev',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='powers.power'),
        ),
        migrations.AddField(
            model_name='powerhistory',
            name='parent_power',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='powers.power_full'),
        ),
        migrations.AddField(
            model_name='base_power',
            name='substitutions',
            field=models.ManyToManyField(blank=True, to='powers.FieldSubstitution', verbose_name='Field substitutions'),
        ),
        migrations.AddField(
            model_name='drawback',
            name='substitutions',
            field=models.ManyToManyField(to='powers.FieldSubstitution'),
        ),
        migrations.AddField(
            model_name='enhancement',
            name='substitutions',
            field=models.ManyToManyField(to='powers.FieldSubstitution'),
        ),
        migrations.AddField(
            model_name='parameter',
            name='substitutions',
            field=models.ManyToManyField(to='powers.FieldSubstitution'),
        ),
        migrations.AddField(
            model_name='power',
            name='power_history',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='powers.powerhistory'),
        ),
    ]
