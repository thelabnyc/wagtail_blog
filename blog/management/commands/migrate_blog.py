from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.conf import settings
import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from blog.models import BlogPage, BlogTag, BlogPageTag, BlogIndexPage, BlogCategory, BlogCategoryBlogPage
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from wagtail.wagtailimages.models import Image
"""
This is a management command to migrate a Wordpress site to Wagtail. Two arguments can be used - the site to be migrated and the site it is being migrated to.

Users will first need to make sure the WP REST API(WP API) plugin is installed on the self-hosted Wordpress site to migrate.
Next users will need to create a BlogIndex object in this GUI. This will be used as a parent object for the child blog page objects.
args0 = url of blog to migrate
args1 = title of BlogIndex
"""
class Command(BaseCommand):
	

    def handle(self, *args, **options):
        """gets data from WordPress site"""
        #first create BlogIndexPage object in GUI
        try:
            blog_index = BlogIndexPage.objects.get(title=args[1])
        except BlogIndexPage.DoesNotExist:
            raise CommandError("Have you created an index yet?")
        if args[0].startswith('http://'):
            base_url = args[0]
        else:
            base_url = ''.join(('http://', args[0]))
        posts_url = ''.join((base_url,'/wp-json/posts'))
        tax_url = ''.join((base_url,'/wp-json/taxonomies'))
        #import pdb; pdb.set_trace()
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
            description = post.get('description')
            url_path = args[1] + '/blog/' + slug
            excerpt = post.get('excerpt')
            status = post.get('status')
            body = post.get('content')
            featured_image = post.get('featured_image')
            #get image info from content and create image objects        
            soup = BeautifulSoup(body)
            for img in soup.findAll('img'):
                old_url = img['src']
                #get image filename
                path,file=os.path.split(img['src'])
                new_url = "{{MEDIA_URL}}/wagtail_images/%s" % file
                #replace image sources with MEDIA_URL
                body = body.replace(old_url,new_url)
                alt_tag = img['alt']
                width = img['width']
                height = img['height']
                image = Image.objects.create(title=alt_tag, file=file, width=width, height=height)
            if featured_image:
                header_image = Image.objects.get(title=alt_tag)
            else:
                header_image = None
            #author/user data
            author = post.get('author')
            username = author['username']
            #date user has registered
            registered = author['registered']
            name = author['name']
            first_name = author['first_name']
            last_name = author['last_name']
            avatar = author['avatar']
            #need to turn avatars into image objects as well maybe? I currently do nothing with the data.
            description = author['description']
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name)
            #format the date
            date = post.get('date')[:10]
            date_modified = post.get('modified')
            new_entry = blog_index.add_child(instance=BlogPage(title=title, slug=slug, search_description="description", date=date, body=body, header_image=header_image, owner=user))

            #categories
            categories_for_blog_entry = []
            tags_for_blog_entry = []
            categories = post.get('terms')
            #not all of the posts have categories/tags
            if len(categories) > 0: 
                for record in categories.values():
                    if record[0]['taxonomy'] == 'post_tag':
                        tag_name = record[0]['name']
                        tag_slug = record[0]['slug']
                        new_tag = BlogTag.objects.get_or_create(name=tag_name, slug=tag_slug)
                        tags_for_blog_entry.append(new_tag)
                    if record[0]['taxonomy'] == 'category':
                        category_name = record[0]['name']
                        category_slug = record[0]['slug']
                        new_category = BlogCategory.objects.get_or_create(name=category_name, slug=category_slug)
                        categories_for_blog_entry.append(new_category)

            #loop through list of BlogCategory and BlogTag objects and create BlogCategoryBlogPages(bcbp) for each category and BlogPageTag objects for each tag for this blog page
            for category in categories_for_blog_entry:
                category = category[0]
                connection = BlogCategoryBlogPage.objects.get_or_create(category=category, page=new_entry)
            for tag in tags_for_blog_entry:
                tag = tag[0]
                connection = BlogPageTag.objects.get_or_create(tag=tag, content_object=new_entry)
         
            #save blog entry
            new_entry.save()       
            
