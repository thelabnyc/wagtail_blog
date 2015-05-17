from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
import os
import sys
import json
import requests
from blog.models import BlogPage, BlogTag, BlogPageTag, BlogIndexPage, BlogCategory, BlogCategoryBlogPage
from django.template.defaultfilters import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

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
        generic_user = User.objects.get_or_create(username="admin")
        generic_user = generic_user[0]
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
            #format for url purposes
            formatted_slug = slug.replace("-","_")
            description = post.get('description')
            url_path = args[1] + '/blog/' + formatted_slug
            excerpt = post.get('excerpt')
            status = post.get('status')
            body = post.get('content')
            featured_image = post.get('featured_image')
            #author/user data
            author = post.get('author')
            username = author['username']
            #date user has registered
            registered = author['registered']
            name = author['name']
            first_name = author['first_name']
            last_name = author['last_name']
            avatar = author['avatar']
            description = author['description']
            try:
                user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name)
            except IntegrityError:
                user = User.objects.get(username=username)

            date = post.get('date')[:10]
            date_modified = post.get('modified')
            
            new_entry = blog_index.add_child(instance=BlogPage(title=title, slug=slug, search_description="description", date=date, owner=user))
            #if there is a featured image, add it to the new entry
            if featured_image:
                new_entry.header_image = featured_image
            #images - still working on this
            
            #for image_tag in re.findall("(<img\s[^>]*?src\s*=\s*['\"]([^'\"]*?)['\"][^>]*?>)", body):
            #    image_tag_text = image_tag[0]
            #    image_tag_src = image_tag[1]
            #    filename = re.findall("/([^/]*)$", image_tag_src)[0]
            #    urllib.urlretrieve(image_tag_src, os.path.join(settings.MEDIA_ROOT, "images", filename))
            #    new_url = settings.MEDIA_URL + 'images/' + filename
            #    body = body.replace(image_tag_src, new_url)            
            
            #categories
            categories_for_blog_entry = []
            tags_for_blog_entry = []
            categories = post.get('terms')
            if len(categories) > 0: 
                for record in categories.values():
                    if record[0]['taxonomy'] == 'post_tag':
                        tag_name = record[0]['name']
                        tag_slug = record[0]['slug']
                        new_tag = BlogPageTag.objects.get_or_create(name=tag_name, slug=tag_slug, content_object=new_entry)
                        tags_for_blog_entry.append(new_tag)
                    if record[0]['taxonomy'] == 'category':
                        print('category')
                        category_name = record[0]['name']
                        category_slug = record[0]['slug']
                        new_category = BlogCategory.objects.get_or_create(name=category_name, slug=category_slug)
                        categories_for_blog_entry.append(new_category)

            #loop through categories_for_blog_entry and create BlogCategoryBlogPages(bcbp) for each category for this blog page
            bcbp = []
            for category in categories_for_blog_entry:
                category = category[0]
                connection = BlogCategoryBlogPage.objects.create(category=category, page=new_entry)
                bcbp.append(connection)
            
            #save BlogCategoryBlogPage objects
            for blog_category in bcbp:
                blog_category.save()
            for blog_tag in tags_for_blog_entry:
                blog_tag.save()
            #save blog entry
            new_entry.save()       
            
