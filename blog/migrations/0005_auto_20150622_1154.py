# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0001_initial'),
        ('blog', '0004_auto_20150427_2047'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlogTag',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('taggit.tag',),
        ),
        migrations.AddField(
            model_name='blogpage',
            name='blog_categories',
            field=models.ManyToManyField(blank=True, through='blog.BlogCategoryBlogPage', to='blog.BlogCategory'),
        ),
        migrations.AlterField(
            model_name='blogcategory',
            name='parent',
            field=models.ForeignKey(blank=True, related_name='children', null=True, to='blog.BlogCategory', help_text='Categories, unlike tags, can have a hierarchy. You might have a Jazz category, and under that have children categories for Bebop and Big Band. Totally optional.'),
        ),
        migrations.AlterField(
            model_name='blogpage',
            name='date',
            field=models.DateField(default=datetime.datetime.today, verbose_name='Post date', help_text='This date may be displayed on the blog post. It is not used to schedule posts to go live at a later date.'),
        ),
    ]
