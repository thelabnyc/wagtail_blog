from django.core.management.base import BaseCommand, CommandError
import os
import sys
import json
import requests
from blog.models import BlogPage, BlogPageTag, BlogIndexPage, BlogCategory, BlogCategoryBlogPage
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
        try:
            fetched_posts = requests.get(posts_url)
        except ConnectionError:
            raise CommandError('There was a problem with the blog entry url.')
            pass
        posts = fetched_posts.json()


        #still testing this
        try:
            fetched_tags_and_categories = requests.get(tax_url)
        except ConnectionError:
            raise CommandError('There was a problem with the taxonomy URL')

        taxonomies = fetched_tags_and_categories.json()
        """
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
       # new_category = blog_index.add_child(instance=BlogCategory(name="newcaadfasfsdftegory", slug="somekindofuniqueslug"))
        new_category = BlogCategory.objects.create(name="slkjfsdkjlskdjflkdj", slug="slkjflskjdflksjdflksjdflkdsj")
        
               
 
     
        
        
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
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name)
            date = post.get('date')[:10]
            date_modified = post.get('modified')
            
            new_entry = blog_index.add_child(instance=BlogPage(title=title, slug=slug, search_description="description", date=date, url_path=url_path, depth=4, owner=user))
            #categories
            categories = post.get('terms')
            categories_for_blog_entry = []
            for c in categories.values():
                category_name = c[0]['name']
                category_slug = c[0]['slug']
                new_category = BlogCategory.objects.create(name=category_name, slug=category_slug)   
                categories_for_blog_entry.append(new_category)            


            #loop through categories_for_blog_entry and create BlogCategoryBlogPages(bcbp) for each category for this blog page
            bcbp = []
            for category in categories_for_blog_entry:
                connection = BlogCategoryBlogPage.objects.create(category=category, page=new_entry)
                bcbp.append(connection)
            
            #save BlogCategoryBlogPage objects
            for each in bcbp:
                each.save()
            #save blog entry
            new_entry.save()       
             
