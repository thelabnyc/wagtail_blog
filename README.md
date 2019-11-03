# Wagtail Blog

[![pipeline status](https://gitlab.com/thelabnyc/wagtail_blog/badges/master/pipeline.svg)](https://gitlab.com/thelabnyc/wagtail_blog/commits/master)

A WordPress-like blog app implemented in Wagtail.

# What is it

After reimplementing WordPress-like blogs over and over again in Wagtail I decided to just make this.
Feel free to use as is or copy it as a starting point. 
It's based on the Wagtail demo blog but is closer to a standard WordPress blog style. 

This is a starting point for your wagtail based blog, especially if you are migrating from Wordpress. It's not Wordpress and it's not drop in. You are expected to add your own templates and are given on a skeleton template to start from.

## Features

- Categories and tags with views
- RSS
- Basic starter templates with pagination
- Comments
- WordPress importer

# Installation

You should start with a existing wagtail django project and have a basic understanding of Wagtail before starting.
See http://docs.wagtail.io

Tested with Wagtail 2.x and Django 2.2.

1. `pip install wagtail-blog`
2. Add `blog` to INSTALLED_APPS
3. Add `url(r'^blog/', include('blog.urls', namespace="blog")),` to urls.py
4. `python manage.py migrate`
5. Override [templates](/blog/templates/blog/) as needed.

## Extending

Wagtail blog features abstract base models. If you want to change functionality you may extend this models from `blog.abstract` and use them how you'd like. Do not add `blog` to your INSTALLED_APPS if you do this. You'll need to create your own logic to gather context variables. See blog/models.py for an example of this. Wagtail blog doesn't support any way to "drop in" the blog app and just make minor changes to models.

# Settings

- `BLOG_PAGINATION_PER_PAGE` (Default 10) Set to change the number of blogs per page. Set to None to disable (useful if using your own pagination implementation).
- `BLOG_LIMIT_AUTHOR_CHOICES_GROUP` Optionally set this to limit the author field choices based on this Django Group. Otherwise it defaults to check if user is_staff. Set to a tuple to allow multiple groups.
- `BLOG_LIMIT_AUTHOR_CHOICES_ADMIN` Set to true if limiting authors to multiple groups and want to add is_staff users as well.

# Import from WordPress

The v2 API is the recommended way to import. It has a cleaner, more recent implementation that is easy to extend as needed.
The v1 API and xml import use an older, less maintained, codebase and are kept here just in case they are useful to anyone.

## Wordpress API v2

This method works with any reasonably modern Wordpress instance and requires no changes to Wordpress and no authentication is needed. It's tested in both wordpress.com and privately hosted Wordpress instances.

### Usage

Use the Django management command `import_wordpress` and provide the slug of the Blog Index Page you wish to add the pages to. For example if you made a Blog Index Page called "blog" and wanted to import my personal wordpress.com hosted blog run:

`./manage.py import_wordpress blog --url=https://public-api.wordpress.com/wp/v2/sites/davidmburke.com`

Notice the special wordpress.com url schema. For a private wordpress instance it would typically look like `https://example.com/wp-json/wp/v2` instead.

**Optional Arguments**

- --convert-images (False) set to True to attempt converting images to Wagtail Image objects. Requires `beautifulsoup4`.
- --create-users (False) set to True to create new users out of authors.

**Extending**

See [wordpress_import.py](/blog/wordpress_import.py). This project can't predict how you host images or implement comments. It's intended to be modified to suit your project's needs.

## JSON API Import

*Legacy feature*

The import feature requires `django-contrib-comments` and `django-comments-xtd`

1. Enable WordPress JSON API
2. Create a Blog index page and note the title. Let's pretend my blog index page title is "blog"
3. Run `./manage.py wordpress_to_wagtail blog --url=http://myblog.com username password` the username is your WordPress username with full access to the API. Without this you can't access all blog posts.

This works by getting the json data for your posts and making Wagtail pages for them. 
It then downloads any images it finds and replaces urls to use your site instead of an external site. 
Blog authors will become Django users.
This is a complex process and is prone to error. You should plan to review the import code and fix some issues.
Merge requests welcome to improve this feature.

## XML file import

*Legacy feature*

1. Create a WordPress XML dump by selecting "export" from the "Tools" section 
of the WordPress admin page.
2. Create a Blog index page and note the title. Let's pretend my blog index page title is "blog"
3. Run `./manage.py wordpress_to_wagtail blog --xml=export.xml` where export.xml is the XML export file from your source WordPress site. 

The xml importer uses the lxml library.

This feature was tested on wordpress XML exports from exactly a few sites.
Like the import procedure above, this process is complex and prone to error.

# Comments

django-comments-xtd comments work out of the box. Just install it as directed [here](http://django-comments-xtd.readthedocs.org/en/latest/). 
Customizing the xtd comment templates should be all you need - but feel free to review this app's templates which you may want to override.

Feel free to contribute other comment implementations.

# Development and Contributing

The included docker-compose file should make it easy to get up and running. 

1. Install docker and docker-compose
2. `docker-compose up`
3. `docker-compose run --rm web ./manage.py migrate`
4. `docker-compose run --rm web ./manage.py createsuperuser`
5. Log in and create a blog index page with blog pages to see a very basic implementation.

Please submit issues and merge requests only on [gitlab](https://gitlab.com/thelabnyc/wagtail_blog). The github page is a read only mirror.

A good merge request should have:

- Based off of the master branch. It should contain only changes that are yours and not from merging.
- Include tests whenever possible. Are you fixing a bug? Add a test that breaks before your patch and works after.
