# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blogcategory',
            options={'ordering': ['name'], 'verbose_name_plural': 'Blog Categories'},
        ),
        migrations.AddField(
            model_name='blogpage',
            name='date',
            field=models.DateField(verbose_name='Post date', default=datetime.datetime(2015, 2, 26, 23, 5, 30, 771014)),
            preserve_default=False,
        ),
    ]
