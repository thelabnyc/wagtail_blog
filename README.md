# wagtail_blog
A wordpress like blog app implemented in wagtail.

# What is it

After reimplimenting wordpress like blogs over and over again in wagtail I decided to just make this. 
Feel free to use as is or copy it as a starting point. 
It's based on the wagtail demo blog but is closer to a standard Wordpress blog style. 

## Features

- Categories and tags with views
- RSS
- Basic starter templates with pagination
- Comments

Work in progress?

- Wordpress importer
- Disqus comments

# Installation

1. `pip install wagtail-blog`
2. Add `blog` to INSTALLED_APPS
3. Add `url(r'^blog/', include('blog.urls')),` to urls.py
4. Override [templates](/blog/templates/blog/) as needed.

# Settings

`BLOG_PAGINATION_PER_PAGE` (Default 10) Set to change the number of blogs per page. Set to None to disable (useful if using your own pagination implimentation).

# Comments

django-comments-xtd comments work out of the box. Just install it as directed [here](http://django-comments-xtd.readthedocs.org/en/latest/). 
Customizing the xtd comment templates should be all you need - but feel free to review this apps templates which you may want to override.

Out of box Disqus coming someday - but it's pretty easy to add manually following the Disqus documentation and overriding templates.

Feel free to contribute other comment implimentations.

# Hacking

The included docker-compose file should make it easy to get up and running. 

1. Install docker and docker-compose
2. `docker-compose up`
3. `docker-compose run --rm web ./manage.py migrate`
4. `docker-compose run --rm web ./manage.py createsuperuser`
5. Log in and create a blog index page with blog pages to see a very basic implimentation.
