from django.core.management.base import BaseCommand, CommandError
import os
import sys
import json
import requests
from blog.models import BlogPage, BlogPageTag, BlogIndexPage, BlogCategory
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

"""
This is a management command to migrate a Wordpress site to Wagtail. Two arguments can be used - the site to be migrated and the site it is being migrated to.

Users will first need to make sure the WP REST API(WP API) plugin is installed on the self-hosted Wordpress site to migrate.

args0 = url of blog to migrate
args1 = title of BlogIndex
"""
class Command(BaseCommand):
	

    def handle(self, *args, **options):
        """gets data from WordPress site"""
        #first create BlogIndexPage object in GUI
        try:
            blog_index = BlogIndexPage.objects.get(title=args[1])
        except IndexDoesNotExist:
            raise CommandError("Have you created an index yet?")
        generic_user = User.objects.get_or_create(username="admin")
        generic_user = generic_user[0]
        print(generic_user)
        if args[0].startswith('http://'):
            base_url = args[0]
        else:
            base_url = ''.join(('http://', args[0]))
        print(base_url)
        posts_url = ''.join((base_url,'/wp-json/posts'))
        tax_url = ''.join((base_url,'/wp-json/taxonomies'))
        try:
            fetched_posts = requests.get(posts_url)
        except ConnectionError:
            raise CommandError('There was a problem with the blog entry url.')
            pass
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
            new_entry = blog_index.add_child(instance=BlogPage(title=title, slug=slug, search_description="description", first_published_at=date, latest_revision_created_at=date_modified, path=int("00100010001"), date=date, url_path=url_path, depth=4, owner=generic_user))
            
            #new_entry.save()
                   
            #Get site taxonomies - includes tags and categories.
            #Gets whichever taxonomies are registered on the site 
                
            #Might go ahead and grab this data first and then add it when creating BlogPage objects
        """
        #still testing this
        try:
            fetched_tags_and_categories = requests.get(tax_url)
        except ConnectionError:
            raise CommandError('There was a problem with the taxonomy URL')

        taxonomies = fetched_tags_and_categories.json()

        for t in taxonomies:
            if t['name'] == 'Categories':
                name = t.get('name')
                slug = t.get('slug')
                parent_item = t.get('parent_item')
                category = BlogCategory.objects.create(name=name, slug=slug, parent_item=parent_item)
                category.save()
                    if t['name'] == 'Tags':
                        name = t.get('name')
                        slug = t.get('slug')
                        parent_item = t.get('parent_item')
                        tag = BlogPageTag.objects.create(name=name, slug=slug, parent_item=parent_item)
                        tag.save()
        
                          
              
               
 
     
        """
