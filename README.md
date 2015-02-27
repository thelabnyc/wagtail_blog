# wagtail_blog
A wordpress like blog app implemented in wagtail.

This is an initial release and will likely change. Use at your own risk.

# What is it

After reimplimenting wordpress like blogs over and over again in wagtail I decided to just make this. 
Feel free to use as is or copy it as a starting point. 
It's based on the wagtail demo blog but is closer to a standard Wordpress blog style. 

## Features

- Categories and tags with views
- RSS
- Basic starter templates with pagination

Work in progress?

- Wordpress importer

# Installation

1. `pip install wagtail-blog`
2. Add `blog` to INSTALLED_APPS
3. Add `url(r'blog/', include('blog.urls')),` to urls.py
4. Override templates as needed.
