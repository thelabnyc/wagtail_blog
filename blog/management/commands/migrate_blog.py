from django.core.management.base import BaseCommand, CommandError
import os
import sys
import json
import requests
from blog.models import BlogPage, BlogPageTag, BlogIndexPage
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

"""
This is a management command to migrate a Wordpress site to Wagtail. Two arguments can be used - the site to be migrated and the site it is being migrated to.

Users will first need to make sure the WP REST API(WP API) plugin is installed on the self-hosted Wordpress site to migrate.
"""
class Command(BaseCommand):
	

    def handle(self, *args, **options):
        """gets data from WordPress site"""
        generic_user = User.objects.get_or_create(username="admin")
        generic_user = generic_user[0]
        print(generic_user)
        if args[0].startswith('http://'):
            base_url = args[0]
        else:
            base_url = ''.join(('http://', args[0]))
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
            #format for url purposes
            formatted_slug = slug.replace("-","_")
            description = post.get('description')
            url_path = args[1] + '/blog/' + formatted_slug
            excerpt = post.get('excerpt')
            status = post.get('status')
            body = post.get('content')
            author = post.get('author')
            owner = author['username']
            #author data comes in a dictionary - could create user objects with this 
            date = post.get('date')[:10]
            date_modified = post.get('modified')
            content_obj = ContentType.objects.get_for_model(model=BlogPage)
            new_entry = BlogPage.objects.create(id=1, content_type=content_obj, title=title, slug=slug, search_description="description", first_published_at=date, latest_revision_created_at=date_modified, depth=1, date=date, url_path=url_path, path=url_path, owner=generic_user)
            #need to first set up the parent - can't create children without a parent
            #new_entry.save()
            #Get site taxonomies - includes tags and categories.
            #Gets whichever taxonomies are registered on the site 
                
            #Might go ahead and grab this data first and then add it when creating BlogPage objects
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
		    
		    
               
 """              
               
 
