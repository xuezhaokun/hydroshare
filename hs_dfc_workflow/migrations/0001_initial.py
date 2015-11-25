# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IrodsWorkflowProcessors',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('irodsProcessorsNumber', models.PositiveIntegerField(max_length=200, null=True, verbose_name=b'iRODS Processors number', blank=True)),
                ('irodsProcessorsType', models.CharField(max_length=200, null=True, verbose_name=b'iRODS Processors type', blank=True)),
                ('irodsProcessorsDescription', models.TextField(verbose_name=b'iRODS Processors description')),
                ('has_CodeRepository', models.BooleanField(default=False, verbose_name=b'Has code repository?')),
                ('codeRepositoryURI', models.URLField(null=True, verbose_name=b'Code repository URI', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_dfc_workflow_irodsworkflowprocessors_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkflowInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('inputType', models.CharField(max_length=200, null=True, verbose_name=b'Input files type', blank=True)),
                ('inputDescription', models.TextField(verbose_name=b'Input files description')),
                ('content_type', models.ForeignKey(related_name='hs_dfc_workflow_workflowinput_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkflowOutput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('outputType', models.CharField(max_length=200, null=True, verbose_name=b'Output files type', blank=True)),
                ('outputDescription', models.TextField(verbose_name=b'Output files description')),
                ('content_type', models.ForeignKey(related_name='hs_dfc_workflow_workflowoutput_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WorkflowProcessors',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('processorsNumber', models.PositiveIntegerField(max_length=200, null=True, verbose_name=b'Processors number', blank=True)),
                ('processorsType', models.CharField(max_length=200, null=True, verbose_name=b'Processors type', blank=True)),
                ('processorsDescription', models.TextField(verbose_name=b'Processors description')),
                ('has_CodeRepository', models.BooleanField(default=False, verbose_name=b'Has code repository?')),
                ('codeRepositoryURI', models.URLField(null=True, verbose_name=b'Code repository URI', blank=True)),
                ('has_DockerImage', models.BooleanField(default=False, verbose_name=b'Has Docker image?')),
                ('dockerImageURI', models.URLField(null=True, verbose_name=b'Docker image URI', blank=True)),
                ('content_type', models.ForeignKey(related_name='hs_dfc_workflow_workflowprocessors_related', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
