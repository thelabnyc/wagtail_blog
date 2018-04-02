# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import datetime


def default_author(apps, schema_editor):
    BlogPage = apps.get_model('blog', 'BlogPage')
    for blog in BlogPage.objects.all():
        if not blog.author:
            blog.author = blog.owner
            blog.save()


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
            name='author',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT),
        ),
        migrations.AddField(
            model_name='blogpage',
            name='blog_categories',
            field=models.ManyToManyField(to='blog.BlogCategory', blank=True, through='blog.BlogCategoryBlogPage'),
        ),
        migrations.AlterField(
            model_name='blogcategory',
            name='parent',
            field=models.ForeignKey(to='blog.BlogCategory', help_text='Categories, unlike tags, can have a hierarchy. You might have a Jazz category, and under that have children categories for Bebop and Big Band. Totally optional.', related_name='children', null=True, blank=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='blogpage',
            name='date',
            field=models.DateField(default=datetime.datetime.today, help_text='This date may be displayed on the blog post. It is not used to schedule posts to go live at a later date.', verbose_name='Post date'),
        ),
        migrations.RunPython(default_author, reverse_code=migrations.RunPython.noop),
    ]
