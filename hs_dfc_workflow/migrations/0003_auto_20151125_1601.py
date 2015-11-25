# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_dfc_workflow', '0002_dfcworkflowmetadata_dfcworkflowresource'),
    ]

    operations = [
        migrations.AlterField(
            model_name='irodsworkflowprocessors',
            name='irodsProcessorsNumber',
            field=models.PositiveIntegerField(default=1, max_length=200, null=True, verbose_name=b'iRODS Processors number', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='workflowprocessors',
            name='processorsNumber',
            field=models.PositiveIntegerField(default=1, max_length=200, null=True, verbose_name=b'Processors number', blank=True),
            preserve_default=True,
        ),
    ]
