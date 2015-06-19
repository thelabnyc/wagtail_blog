from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.conf import settings 
import urllib.request 
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

    #can_import_settings = True    

    def add_arguments(self, parser):
        """have to add this to use args in django 1.8"""
        parser.add_argument('blog_to_migrate')
        parser.add_argument('blog_index')	

    def handle(self, *args, **options):
        """gets data from WordPress site"""
        #first create BlogIndexPage object in GUI
        try:
            blog_index = BlogIndexPage.objects.get(title=options['blog_index'])
        except BlogIndexPage.DoesNotExist:
            raise CommandError("Have you created an index yet?")
        posts = self.get_posts_data(options['blog_to_migrate'])
        self.create_blog_pages(posts, blog_index)

    def convert_html_entities(self, text, *args, **options):
        """converts html symbols so they show up correctly in wagtail"""
        list_of_symbols = {'&#8221;': ' ', '&8217;': "'", '&lt;': '<', '&#60;': '<', '&gt;': '>', '&#62;': '>', '&#47;': '/', '&#93;': ']', '&#91;': '[', '&quot;': '"', '&#34;': '"', '&#39;': '\'', '&ldquo;': '“', '&#8220;': '“', '&rdquo;': '”', '&#8220;': '”', '&amp;': '&', '&#38;': '&', '&lsquo;': "'", '&#8216;': "'", '&rsquo;': "'", '&#8217;': "'", '&#038;': '&'}
        for i,j in list_of_symbols.items():
            if i in text:
                text = text.replace(i, j)
        return text

  
    def get_posts_data(self, blog, *args, **options):
        self.url = blog         
        headers = {
            #'Authorization': 'Bearer {}'.format(settings.WP_API_AUTH_TOKEN)
        }
        if self.url.startswith('http://'):
            base_url = url
        else:
            base_url = ''.join(('http://', self.url))
        posts_url = ''.join((base_url,'/wp-json/posts'))
        try:
            fetched_posts = requests.get(posts_url, headers=headers)
        except ConnectionError:
            raise CommandError('There was a problem with the blog entry url.')
            pass
        return fetched_posts.json()
        
    def create_images_from_urls_in_content(self, body):
        """create Image objects and transfer image files to media root"""
        images_that_did_not_migrate = []
        soup = BeautifulSoup(body)
        for img in soup.findAll('img'):
            old_url = img['src']
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
            try:
                path,file=os.path.split(img['src'])
                #copy image file over to MEDIA_ROOT location
                copy_image = os.path.join(settings.MEDIA_ROOT, file)
                website = urllib.request.urlretrieve(img['src'], os.path.join(settings.MEDIA_ROOT, file))
                image = Image.objects.get_or_create(title=file, file=website[0], width=width, height=height)
                image[0].save()
                new_url = settings.MEDIA_URL + file
            except FileNotFoundError:
                #if there is a problem and the file doesn't migrate, leave the old URL as is
                new_url = old_url
                images_that_did_not_migrate.append(img)
                pass
            #replace image sources with MEDIA_URL
            body = body.replace(old_url,new_url) 
            body = self.convert_html_entities(body)
            #returns body content with new img tags, as well as a list of any images that were not migrated for whatever reason
        return body, images_that_did_not_migrate
            
    def create_user(self, author):
        username = author['username']
        #date user registered on site
        registered = author['registered']
        name = author['name']
        first_name = author['first_name']
        last_name = author['last_name']
        description = author['description']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name)
        
        
    def create_categories_and_tags(self, page, categories):
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
        """create Blog post entries from wordpress data"""
        for post in posts:
            title = post.get('title')
            if title:
                new_title = self.convert_html_entities(title)
                title = new_title
            slug = post.get('slug')
            description = post.get('description')
            if description:
                description = self.convert_html_entities(description)
            excerpt = post.get('excerpt')
            status = post.get('status')
            body = post.get('content')
            #get image info from content and create image objects  
            new_body = self.create_images_from_urls_in_content(body)
            #body content returned after images created has updated URLs in the image tags
            body = new_body[0]
            #author/user data
            author = post.get('author')
            user = self.create_user(author)
            categories = post.get('terms')
            #format the date
            date = post.get('date')[:10]
            date_modified = post.get('modified')
            try:
                new_entry = BlogPage.objects.get(slug=slug)
            except BlogPage.DoesNotExist:    
                new_entry = blog_index.add_child(instance=BlogPage(title=title, slug=slug, search_description="description", date=date, body=body, owner=user))
            featured_image = post.get('featured_image')      
            if featured_image is not None:
                title = post['featured_image']['title']
                source = post['featured_image']['source']
                path,file=os.path.split(source)
                #copy image file over to MEDIA_ROOT location
                copy_image = os.path.join(settings.MEDIA_ROOT, file)
                website = urllib.request.urlretrieve(source, os.path.join(settings.MEDIA_ROOT, file))
                width = 640
                height = 290
                try:
                    header_image = Image.objects.get_or_create(title=title, width=width, height=height, file=website[0])
                    header_image = header_image[0]
                except Image.DoesNotExist:
                    print("Could not find the Featured Image for post %s in wagtail images" % title)
                    header_image = None
            else:
                header_image = None
            new_entry.header_image = header_image
            new_entry.save()
            self.create_categories_and_tags(new_entry, categories)   
            
           

