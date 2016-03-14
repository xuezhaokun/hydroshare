# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_dfc_workflow', '0003_auto_20151125_1601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='irodsworkflowprocessors',
            name='irodsProcessorsNumber',
            field=models.PositiveIntegerField(default=1, null=True, verbose_name=b'iRODS Processors number', blank=True),
        ),
        migrations.AlterField(
            model_name='workflowprocessors',
            name='processorsNumber',
            field=models.PositiveIntegerField(default=1, null=True, verbose_name=b'Processors number', blank=True),
        ),
    ]
