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

Things you could contribute:

- Disqus comments

# Installation

You should start with a existing wagtail django project and have a basic understanding of Wagtail before starting.
See http://docs.wagtail.io

For Wagtail 2 and Django 1.11+ use wagtail-blog 2.x

For Wagtail 1.x use wagtail-blog 1.7.x

1. `pip install wagtail-blog`
2. Add `blog` to INSTALLED_APPS
3. Add `url(r'^blog/', include('blog.urls', namespace="blog")),` to urls.py
4. `python manage.py migrate`
5. Override [templates](/blog/templates/blog/) as needed.

# Settings

- `BLOG_PAGINATION_PER_PAGE` (Default 10) Set to change the number of blogs per page. Set to None to disable (useful if using your own pagination implementation).
- `BLOG_LIMIT_AUTHOR_CHOICES_GROUP` Optionally set this to limit the author field choices based on this Django Group. Otherwise it defaults to check if user is_staff. Set to a tuple to allow multiple groups.
- `BLOG_LIMIT_AUTHOR_CHOICES_ADMIN` Set to true if limiting authors to multiple groups and want to add is_staff users as well.

# Import from WordPress

The import feature requires `django-contrib-comments` and `django-comments-xtd`

## JSON API Import

1. Enable WordPress JSON API
2. Create a Blog index page and note the title. Let's pretend my blog index page title is "blog"
3. Run `./manage.py wordpress_to_wagtail blog --url=http://myblog.com username password` the username is your WordPress username with full access to the API. Without this you can't access all blog posts.

This works by getting the json data for your posts and making Wagtail pages for them. 
It then downloads any images it finds and replaces urls to use your site instead of an external site. 
Blog authors will become Django users.
This is a complex process and is prone to error. You should plan to review the import code and fix some issues.
Merge requests welcome to improve this feature.

## XML file import

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

Out of box Disqus coming someday - but it's pretty easy to add manually following the Disqus documentation and overriding templates.

Feel free to contribute other comment implimentations.

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
