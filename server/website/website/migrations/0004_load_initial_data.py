# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-12-07 19:51


from django.core.management import call_command
from django.db import migrations
import logging

LOG = logging.getLogger(__name__)

def load_initial_data(apps, schema_editor):
    initial_data_fixtures = [
        "dbms_catalog.json",
        "postgres-96_knobs.json",
        "postgres-96_metrics.json",
        "postgres-92_knobs.json",
        "postgres-92_metrics.json",
        "postgres-93_knobs.json",
        "postgres-93_metrics.json",
        "postgres-94_knobs.json",
        "postgres-94_metrics.json",
        "myrocks-5.6_knobs.json",
        "myrocks-5.6_metrics.json",
        "mysql-5.7_knobs_v4.json",
        "mysql-5.7_metrics.json",
        "oracle_knobs.json",
        "oracle_metrics.json"
    ]
    for fixture in initial_data_fixtures:
        call_command("loaddata", fixture, app_label="website")
    LOG.info("***** DATA FIXTURES: Loaded")


def unload_initial_data(apps, schema_editor):
    model_names = [
        "DBMSCatalog",
        "KnobCatalog",
        "MetricCatalog",
        "Hardware"
    ]
    for model_name in model_names:
        model = apps.get_model("website", model_name)
        model.objects.all().delete()
    LOG.info("***** INITIAL DATA: Unloaded")


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_background_task_optimization'),
    ]

    operations = [
        migrations.RunPython(load_initial_data, unload_initial_data)
    ]
    LOG.info("***** COMPLETED 0004 MIGRATION")
