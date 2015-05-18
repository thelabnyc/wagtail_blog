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
This is a management command to migrate a Wordpress site to Wagtail. Two arguments should be used - the site to be migrated and the site it is being migrated to.

Users will first need to make sure the WP REST API(WP API) plugin is installed on the self-hosted Wordpress site to migrate.
Next users will need to create a BlogIndex object in this GUI. This will be used as a parent object for the child blog page objects.
args0 = url of blog to migrate
args1 = title of BlogIndex that you created in the GUI
"""
class Command(BaseCommand):
	

    def handle(self, *args, **options):
        """gets data from WordPress site"""
        #first create BlogIndexPage object in GUI
        try:
            blog_index = BlogIndexPage.objects.get(title=args[1])
        except BlogIndexPage.DoesNotExist:
            raise CommandError("Have you created an index yet?")
        posts = self.get_posts_data(args[0])
        self.create_blog_pages(posts, blog_index)
            
    def get_posts_data(self, *args):
        """get json data from a given wordpress site"""
        self.url = args[0]        
        if self.url.startswith('http://'):
            base_url = url
        else:
            base_url = ''.join(('http://', args[0]))
        posts_url = ''.join((base_url,'/wp-json/posts'))
        try:
            fetched_posts = requests.get(posts_url)
        except ConnectionError:
            raise CommandError('There was a problem with the blog entry url.')
            pass
        return fetched_posts.json()
        
    def create_images_from_urls_in_content(self, body):
        images_that_did_not_migrate = []
        soup = BeautifulSoup(body)
        for img in soup.findAll('img'):
            old_url = img['src']
            #get image filename
            try:
                path,file=os.path.split(img['src'])
                new_url = "{{MEDIA_URL}}/wagtail_images/%s" % file
            except FileNotFoundError:
                new_url = "{{MEDIA_URL}}/wagtail_images/"
                images_that_did_not_migrate.append(img)
            #replace image sources with MEDIA_URL
            body = body.replace(old_url,new_url)
            if 'alt_tag' in img:
                alt_tag = img['alt']
            else:
                alt_tag = ""
            if 'width' in img:
                width = img['width']
            if 'height' in img:
                height = img['height']
            else:
                width = 100
                height = 100
            image = Image.objects.create(title=alt_tag, file=file, width=width, height=height)
            print(Image.objects.filter(title=alt_tag)) 
        return body, images_that_did_not_migrate
            
    def create_user(self, author):
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
        return
        
    def create_categories_and_tags(self, page, categories):
        #categories
        categories_for_blog_entry = []
        tags_for_blog_entry = []
        #not all of the posts have categories/tags
        if len(categories) > 0: 
            for record in categories.values():
                if record[0]['taxonomy'] == 'post_tag':
                    tag_name = record[0]['name']
                    tag_slug = record[0]['slug']
                    new_tag = BlogTag.objects.get_or_create(name=tag_name, slug=tag_slug)
                    tags_for_blog_entry.append(new_tag)
                if record[0]['taxonomy'] == 'category':
                    print(record)
                    category_name = record[0]['name']
                    
                    category_slug = record[0]['slug']
                    new_category = BlogCategory.objects.get_or_create(name=category_name, slug=category_slug)
                    categories_for_blog_entry.append(new_category)
        #loop through list of BlogCategory and BlogTag objects and create BlogCategoryBlogPages(bcbp) for each category and BlogPageTag objects for each tag for this blog page
        for category in categories_for_blog_entry:
            category = category[0]
            connection = BlogCategoryBlogPage.objects.get_or_create(category=category, page=page)
        for tag in tags_for_blog_entry:
            tag = tag[0]
            connection = BlogPageTag.objects.get_or_create(tag=tag, content_object=page)
        return "Categories and Tags Printed"

    def create_blog_pages(self, posts, blog_index, *args):
        #create BlogPage object for each record
        for post in posts:
            title = post.get('title')
            slug = post.get('slug')
            description = post.get('description')
            excerpt = post.get('excerpt')
            status = post.get('status')
            body = post.get('content')
            #get image info from content and create image objects  
            self.create_images_from_urls_in_content(body)
            print("Creating Images")
            #author/user data
            author = post.get('author')
            user = self.create_user(author)
            categories = post.get('terms')
            #format the date
            date = post.get('date')[:10]
            date_modified = post.get('modified')
            new_entry = blog_index.add_child(instance=BlogPage(title=title, slug=slug, search_description="description", date=date, body=body, owner=user))
            featured_image = post.get('featured_image')      
            if featured_image is not None:
                title = post['featured_image']['title']
                try:
                    header_image = Image.objects.get(title=title)
                except Image.DoesNotExist:
                    print("Could not find the Featured Image for post %s in wagtail images" % title)
                    header_image = None
            else:
                header_image = None
            new_entry.header_image = header_image
            new_entry.save()
            print("Saving New BlogPage entry")
            self.create_categories_and_tags(new_entry, categories)   
            print("Creating categories and tags for the entry")
           
            
