# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0027_auto_20160818_2308'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='action_done',
            field=models.BooleanField(default=False),
        ),
    ]
