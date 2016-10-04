# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0028_baseresource_action_done'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='baseresource',
            name='action_done',
        ),
        migrations.AddField(
            model_name='baseresource',
            name='model_output_path_in_user_zone',
            field=models.CharField(default=b'', max_length=100, blank=True),
        ),
    ]
