# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0013_auto_20151114_2314'),
        ('hs_dfc_workflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DFCWorkflowMetaData',
            fields=[
                ('coremetadata_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='hs_core.CoreMetaData')),
            ],
            options={
            },
            bases=('hs_core.coremetadata',),
        ),
        migrations.CreateModel(
            name='DFCWorkflowResource',
            fields=[
            ],
            options={
                'ordering': ('_order',),
                'verbose_name': 'DFC Workflow Resource',
                'proxy': True,
            },
            bases=('hs_core.baseresource',),
        ),
    ]
