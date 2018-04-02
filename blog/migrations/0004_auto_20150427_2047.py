# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import wagtail.core.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_auto_20150323_2116'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blogcategory',
            options={'ordering': ['name'], 'verbose_name_plural': 'Blog Categories', 'verbose_name': 'Blog Category'},
        ),
        migrations.AlterModelOptions(
            name='blogindexpage',
            options={'verbose_name': 'Blog index'},
        ),
        migrations.AlterModelOptions(
            name='blogpage',
            options={'verbose_name_plural': 'Blog pages', 'verbose_name': 'Blog page'},
        ),
        migrations.AddField(
            model_name='blogcategory',
            name='description',
            field=models.CharField(max_length=500, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='blogcategory',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, to='blog.BlogCategory', help_text='Categories, unlike tags, can have a hierarchy. You might have a Jazz category, and under that have children categories for Bebop and Big Band. Totally optional.', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='blogcategoryblogpage',
            name='category',
            field=models.ForeignKey(verbose_name='Category', related_name='+', to='blog.BlogCategory', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='blogpage',
            name='body',
            field=wagtail.core.fields.RichTextField(verbose_name='body'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='blogpage',
            name='header_image',
            field=models.ForeignKey(to='wagtailimages.Image', verbose_name='Header image', blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+'),
            preserve_default=True,
        ),
    ]
