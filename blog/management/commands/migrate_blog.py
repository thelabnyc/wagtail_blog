from django.core.management.base import BaseCommand, CommandError
import os
import sys
import json
import requests
from wagtail_blog.models import BlogPage, BlogPageTag, BlogIndexPage
from django.template.defaultfilters import slugify
from django.db.utils import IntegrityError


"""
This is a management command to migrate a Wordpress site to Wagtail. 

"""

class Command(BaseCommand):
	
	
	def handle(self, *args, **options):
		"""gets data from WordPress site"""
		#need to get install plugin to get site info
		query_string = "https://public-api.wordpress.com/rest/v1.1/%s" % site_info
		#I copied the headers part from the sternb0t github script - not sure if I will end up needing it
		headers = {
                "Authorization": 'Bearer {}'.format(settings.WP_API_TMP_AUTH_TOKEN)
                }
		result = requests.get(query_string, headers=headers)
		posts =  result.json()
		
		#go through json and make python objects for each Wagtail_blog model
		for post in posts:
		    #going to create BlogPage objects for each record
		    BlogPage.objects.create(...)
		
		
		#request to a url to get blog categories
		categories_query = ""
		categories_result = requests.get(categories_query, headers=headers)
		categories = categories_result.json()
		#create BlogCategory objects, make sure we don't have repeats, etc
		for c in categories:
		    #make sure no duplicates
		    BlogCategory.objects.create(...)
		
		#request to a different url to get blog tags
		tag_query = ""
		tag_result = requests.get(tag_query, headers=headers)
		tags = tag_result.json()
		for t in tags:
		    #make sure we don't have duplicates
		    BlogPageTag.objects.create(...)
		
		
		#will take care of BlogPageIndex stuff too
		    
		    
               
               
               
               
