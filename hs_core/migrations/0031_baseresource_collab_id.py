# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0030_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='collab_id',
            field=models.CharField(default=b'', max_length=50, blank=True),
        ),
    ]
