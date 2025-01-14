# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2019-08-08 21:47
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0004_load_initial_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dbmscatalog',
            name='type',
            field=models.IntegerField(choices=[(1, 'MySQL'), (2, 'Postgres'), (3, 'Db2'), (4, 'Oracle'), (6, 'SQLite'), (7, 'HStore'), (8, 'Vector'), (5, 'SQL Server'), (9, 'MyRocks')]),
        ),
        migrations.AlterField(
            model_name='hardware',
            name='type',
            field=models.IntegerField(choices=[(1, 'generic'), (2, 't2.nano'), (3, 't2.micro'), (4, 't2.small'), (5, 't2.medium'), (6, 't2.large'), (7, 't2.xlarge'), (8, 't2.2xlarge'), (9, 'm4.large'), (10, 'm4.xlarge'), (11, 'm4.2xlarge'), (12, 'm4.4xlarge'), (13, 'm4.10xlarge'), (14, 'm4.16xlarge'), (15, 'm3.medium'), (16, 'm3.large'), (17, 'm3.xlarge'), (18, 'm3.2xlarge'), (19, 'c4.large'), (20, 'c4.xlarge'), (21, 'c4.2xlarge'), (22, 'c4.4xlarge'), (23, 'c4.8xlarge'), (24, 'c3.large'), (25, 'c3.xlarge'), (26, 'c3.2xlarge'), (27, 'c3.4xlarge'), (28, 'c3.8xlarge'), (29, 'p2.xlarge'), (30, 'p2.8xlarge'), (31, 'p2.16xlarge'), (32, 'g2.2xlarge'), (33, 'g2.8xlarge'), (34, 'x1.16large'), (35, 'x1.32xlarge'), (36, 'r4.large'), (37, 'r4.xlarge'), (38, 'r4.2xlarge'), (39, 'r4.4xlarge'), (40, 'r4.8xlarge'), (41, 'r4.16xlarge'), (42, 'r3.large'), (43, 'r3.xlarge'), (44, 'r3.2xlarge'), (45, 'r3.4xlarge'), (46, 'r3.8xlarge'), (47, 'i3.large'), (48, 'i3.xlarge'), (49, 'i3.2xlarge'), (50, 'i3.4xlarge'), (51, 'i3.8xlarge'), (52, 'i3.16large'), (53, 'd2.xlarge'), (54, 'd2.2xlarge'), (55, 'd2.4xlarge'), (56, 'd2.8xlarge'), (57, 'f1.2xlarge'), (58, 'f1.16xlarge')]),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='default',
            field=models.TextField(verbose_name='default value'),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='enumvals',
            field=models.TextField(null=True, verbose_name='valid values'),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='maxval',
            field=models.CharField(max_length=32, null=True, verbose_name='maximum value'),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='minval',
            field=models.CharField(max_length=32, null=True, verbose_name='minimum value'),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='resource',
            field=models.IntegerField(choices=[(1, 'Memory'), (2, 'CPU'), (3, 'Stroage'), (4, 'Other')], default=4),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='summary',
            field=models.TextField(null=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='tunable',
            field=models.BooleanField(verbose_name='tunable'),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='unit',
            field=models.IntegerField(choices=[(1, 'bytes'), (2, 'milliseconds'), (3, 'other')]),
        ),
        migrations.AlterField(
            model_name='knobcatalog',
            name='vartype',
            field=models.IntegerField(choices=[(1, 'STRING'), (2, 'INTEGER'), (3, 'REAL'), (4, 'BOOL'), (5, 'ENUM'), (6, 'TIMESTAMP')], verbose_name='variable type'),
        ),
        migrations.AlterField(
            model_name='metriccatalog',
            name='metric_type',
            field=models.IntegerField(choices=[(1, 'COUNTER'), (2, 'INFO'), (3, 'STATISTICS')]),
        ),
        migrations.AlterField(
            model_name='metriccatalog',
            name='summary',
            field=models.TextField(null=True, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='metriccatalog',
            name='vartype',
            field=models.IntegerField(choices=[(1, 'STRING'), (2, 'INTEGER'), (3, 'REAL'), (4, 'BOOL'), (5, 'ENUM'), (6, 'TIMESTAMP')]),
        ),
        migrations.AlterField(
            model_name='pipelinedata',
            name='task_type',
            field=models.IntegerField(choices=[(1, 'Pruned Metrics'), (2, 'Ranked Knobs'), (3, 'Knob Data'), (4, 'Metric Data')]),
        ),
        migrations.AlterField(
            model_name='project',
            name='name',
            field=models.CharField(max_length=64, verbose_name='project name'),
        ),
        migrations.AlterField(
            model_name='result',
            name='session',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.Session', verbose_name='session name'),
        ),
        migrations.AlterField(
            model_name='session',
            name='name',
            field=models.CharField(max_length=64, verbose_name='session name'),
        ),
        migrations.AlterField(
            model_name='session',
            name='target_objective',
            field=models.CharField(choices=[('throughput_txn_per_sec', 'Throughput'), ('99th_lat_ms', '99 Percentile Latency')], max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='session',
            name='tuning_session',
            field=models.CharField(choices=[('tuning_session', 'Tuning Session'), ('no_tuning_session', 'No Tuning'), ('randomly_generate', 'Randomly Generate')], default='tuning_sesion', max_length=64),
        ),
        migrations.AlterField(
            model_name='workload',
            name='name',
            field=models.CharField(max_length=128, verbose_name='workload name'),
        ),
    ]
