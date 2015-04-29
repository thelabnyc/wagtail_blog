from django.core.management.base import BaseCommand, CommandErrors
import os
import sys
import json
import requests
from wagtail_blog.models import BlogPage, BlogPageTag, BlogIndexPage
from django.template.defaultfilters import slugify
from django.db.utils import IntegrityError


"""
This is a management command to migrate a Wordpress site to Wagtail. 

Users will first need to make sure the WP REST API(WP API) plugin is installed on the self-hosted Wordpress site to migrate.
"""

class Command(BaseCommand):
	
	def handle(self, *args, **options):
		"""gets data from WordPress site"""
                base_url = args[0]
                posts_url = ''.join((base_url,'/wp-json/posts'))
                tax_url = ''.join((base_url,'/wp-json/taxonomies'))
                try:
                    fetched_posts = requests.get(posts_url)
		except ConnectionError:
                    raise CommandError('There was a problem with the blog entry url.')

		posts = fetched_posts.json()
		#create BlogPage object for each record
		for post in posts:
		    title = post.get('title')
                    slug = post.get('slug')
                    description = post.get('description')
                    excerpt = post.get('excerpt')
                    status = post.get('status')
                    body = post.get('content')
                    author = post.get('author')
                    #author data comes in a dictionary - could create user objects with this 
                    date = post.get('date')
                    date_modified = post.get('modified')

                    #BlogPage.objects.create(...)
		"""
                Get site taxonomies - includes tags and categories.
                Gets whichever taxonomies are registered on the site 
                
                Might go ahead and grab this data first and then add it when creating BlogPage objects
                """
		try:
                    fetched_tags_and_categories = requests.get(tax_url)
                except ConnectionError:
                    raise CommandError('There was a problem with the taxonomy URL')

                taxonomies = fetched_tags_and_categories.json()

                #still figuring out how the wordpress data works for categories and tags
                #might get them from separate URLs
                for t in taxonomies:
                    if t['name'] == 'Categories':
                        name = t.get('name')
                        slug = t.get('slug')
                        parent_item = t.get('parent_item')
                    #if t['name'] == 'Tags':
                           
		#will take care of BlogPageIndex stuff too
		    
		    
               
               
               
               
