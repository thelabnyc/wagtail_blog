from base64 import b64encode

from datetime import datetime
import html
import json
import os
import urllib.request


from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File
from django.contrib.auth import get_user_model
User = get_user_model()
from django.contrib.auth.models import User
from django_comments_xtd.models import XtdComment
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.utils import timezone
from django.utils.html import linebreaks
from django_comments_xtd.models import MaxThreadLevelExceededException


from bs4 import BeautifulSoup
import requests

from blog.models import (BlogPage, BlogTag, BlogPageTag, BlogIndexPage,
                         BlogCategory, BlogCategoryBlogPage)
from wagtail.images.models import Image


class Command(BaseCommand):
    """
    This is a management command to migrate a Wordpress site to Wagtail.
    Two arguments should be used - the site to be migrated and the site it is
    being migrated to.

    Users will first need to make sure the WP REST API(WP API) plugin is
    installed on the self-hosted Wordpress site to migrate.
    Next users will need to create a BlogIndex object in this GUI.
    This will be used as a parent object for the child blog page objects.
    """

    def add_arguments(self, parser):
        """have to add this to use args in django 1.8"""
        parser.add_argument('blog_index',
                            help="Title of blog index page to attach blogs")
        parser.add_argument('--url',
                            default=False,
                            help="Base url of wordpress instance")
        parser.add_argument('--username',
                            default=False,
                            help='Username for basic Auth')
        parser.add_argument('--password',
                            default=False,
                            help='Password for basic Auth')
        parser.add_argument('--import-comments',
                            action="store_true",
                            help="import Wordpress comments to Django Xtd")
        parser.add_argument('--xml',
                            # default='',
                            help="import from XML instead of API")

    def handle(self, *args, **options):
        """gets data from WordPress site"""
        # TODO: refactor these with .get
        if 'username' in options:
            self.username = options['username']
        else:
            self.username = None
        if 'password' in options:
            self.password = options['password']
        else:
            self.password = None

        self.xml_path = options.get('xml')
        self.url = options.get('url')
        try:
            blog_index = BlogIndexPage.objects.get(
                title__icontains=options['blog_index'])
        except BlogIndexPage.DoesNotExist:
            raise CommandError("Incorrect blog index title - have you created it?")
        if self.url == "just_testing":
            with open('test-data.json') as test_json:
                posts = json.load(test_json)
        elif self.xml_path:
            try:
                import lxml
                from blog.wp_xml_parser import XML_parser
            except ImportError as e:
                print("You must have lxml installed to run xml imports."
                      " Run `pip install lxml`.")
                raise e
            self.xml_parser = XML_parser(self.xml_path)
            posts = self.xml_parser.get_posts_data()
        else:
            posts = self.get_posts_data(self.url)
        self.should_import_comments = options.get('import_comments')
        self.create_blog_pages(posts, blog_index)

    def prepare_url(self, url):
        if url.startswith('//'):
            url = 'http:{}'.format(url)
        if url.startswith('/'):
            prefix_url = self.url
            if prefix_url and prefix_url.endswith('/'):
                prefix_url = prefix_url[:-1]
            url = '{}{}'.format(prefix_url or "", url)
        return url

    def convert_html_entities(self, text, *args, **options):
        """converts html symbols so they show up correctly in wagtail"""
        return html.unescape(text)

    def clean_data(self, data):
        # I have no idea what this junk is
        garbage = data.split("[")[0]
        data = data.strip(garbage)
        for bad_data in ['8db4ac', '\r\n', '\r\n0']:
            data = data.strip(bad_data)
        return data

    def get_posts_data(
        self, blog, id=None, get_comments=False, *args, **options
    ):
        if self.url == "just_testing":
            with open('test-data-comments.json') as test_json:
                return json.load(test_json)

        self.url = blog
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.username and self.password:
            auth = b64encode(
                str.encode('{}:{}'.format(self.username, self.password)))
            headers['Authorization'] = 'Basic {}'.format(auth)
        if self.url.startswith('http://'):
            base_url = self.url
        else:
            base_url = ''.join(('http://', self.url))
        posts_url = ''.join((base_url, '/wp-json/posts'))
        comments_url = ''.join((posts_url, '/%s/comments')) % id
        if get_comments is True:
            comments_url = ''.join((posts_url, '/%s/comments')) % id
            fetched_comments = requests.get(comments_url)
            comments_data = fetched_comments.text
            comments_data = self.clean_data(comments_data)
            return json.loads(comments_data)
        else:
            fetched_posts = requests.get(posts_url +
                                         '?filter[posts_per_page]=-1',
                                         headers=headers)
            data = fetched_posts.text
            data = self.clean_data(data)
            return json.loads(data)

    def create_images_from_urls_in_content(self, body):
        """create Image objects and transfer image files to media root"""
        soup = BeautifulSoup(body, "html5lib")
        for img in soup.findAll('img'):
            old_url = img['src']
            if 'width' in img:
                width = img['width']
            if 'height' in img:
                height = img['height']
            else:
                width = 100
                height = 100
            path, file_ = os.path.split(img['src'])
            if not img['src']:
                continue  # Blank image
            if img['src'].startswith('data:'):
                continue # Embedded image
            try:
                remote_image = urllib.request.urlretrieve(
                    self.prepare_url(img['src']))
            except (urllib.error.HTTPError,
                    urllib.error.URLError,
                    UnicodeEncodeError,
                    ValueError):
                print("Unable to import " + img['src'])
                continue
            image = Image(title=file_, width=width, height=height)
            try:
                image.file.save(file_, File(open(remote_image[0], 'rb')))
                image.save()
                new_url = image.file.url
                body = body.replace(old_url, new_url)
                body = self.convert_html_entities(body)
            except TypeError:
                print("Unable to import image {}".format(remote_image[0]))
        return body

    def create_user(self, author):
        username = author['username']
        first_name = author['first_name']
        last_name = author['last_name']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username, first_name=first_name, last_name=last_name)
        return user

    def create_comment(
        self, blog_post_type, blog_post_id, comment_text, date
    ):
        # Assume that the timezone wanted is the one that's active during parsing
        if date is not None and settings.USE_TZ and timezone.is_naive(date):
            date = timezone.make_aware(date, timezone.get_current_timezone())

        new_comment = XtdComment.objects.get_or_create(
            site_id=self.site_id,
            content_type=blog_post_type,
            object_pk=blog_post_id,
            comment=comment_text,
            submit_date=date,
        )[0]
        return new_comment

    def lookup_comment_by_wordpress_id(self, comment_id, comments):
        """ Returns Django comment object with this wordpress id """
        for comment in comments:
            if comment.wordpress_id == comment_id:
                return comment

    def import_comments(self, post_id, slug, *args, **options):
        try:
            mysite = Site.objects.get_current()
            self.site_id = mysite.id
        except Site.DoesNotExist:
            print('site does not exist')
            return
        if getattr(self, 'xml_path', None):
            comments = self.xml_parser.get_comments_data(slug)
        else:
            comments = self.get_posts_data(
                self.url, post_id, get_comments=True)
        imported_comments = []
        for comment in comments:
            try:
                blog_post = BlogPage.objects.get(slug=slug)
                blog_post_type = ContentType.objects.get_for_model(blog_post)
            except BlogPage.DoesNotExist:
                print('cannot find this blog post')
                continue
            comment_text = self.convert_html_entities(comment.get('content'))
            date = datetime.strptime(comment.get('date'), '%Y-%m-%dT%H:%M:%S')
            status = comment.get('status')
            if status != 'approved':
                continue
            comment_author = comment.get('author')
            new_comment = self.create_comment(
                blog_post_type, blog_post.pk, comment_text, date)
            new_comment.wordpress_id = comment.get('ID')
            new_comment.parent_wordpress_id = comment.get('parent')
            if type(comment_author) is int:
                pass
            else:
                if 'username' in comment_author:
                    user_name = comment['author']['username']
                    user_url = comment['author']['URL']
                    try:
                        current_user = User.objects.get(username=user_name)
                        new_comment.user = current_user
                    except User.DoesNotExist:
                        pass

                    new_comment.user_name = user_name
                    new_comment.user_url = user_url

            new_comment.save()
            imported_comments.append(new_comment)
        # Now assign parent comments
        for comment in imported_comments:
            if str(comment.parent_wordpress_id or 0) == "0":
                continue
            for sub_comment in imported_comments:
                if sub_comment.wordpress_id == comment.parent_wordpress_id:
                    comment.parent_id = sub_comment.id
                    try:
                        comment._calculate_thread_data()
                        comment.save()
                    except MaxThreadLevelExceededException:
                        print("Warning, max thread level exceeded on {}"
                              .format(comment.id))
                    break

    def create_categories_and_tags(self, page, categories):
        tags_for_blog_entry = []
        categories_for_blog_entry = []
        for records in categories.values():
            if records[0]['taxonomy'] == 'post_tag':
                for record in records:
                    tag_name = record['name']
                    new_tag = BlogTag.objects.get_or_create(name=tag_name)[0]
                    tags_for_blog_entry.append(new_tag)

            if records[0]['taxonomy'] == 'category':
                for record in records:
                    category_name = record['name']
                    new_category = BlogCategory.objects.get_or_create(name=category_name)[0]
                    if record.get('parent'):
                        parent_category = BlogCategory.objects.get_or_create(
                            name=record['parent']['name'])[0]
                        parent_category.slug = record['parent']['slug']
                        parent_category.save()
                        parent = parent_category
                        new_category.parent = parent
                    else:
                        parent = None
                    categories_for_blog_entry.append(new_category)
                    new_category.save()

        # loop through list of BlogCategory and BlogTag objects and create
        # BlogCategoryBlogPages(bcbp) for each category and BlogPageTag objects
        # for each tag for this blog page
        for category in categories_for_blog_entry:
            BlogCategoryBlogPage.objects.get_or_create(
                category=category, page=page)[0]
        for tag in tags_for_blog_entry:
            BlogPageTag.objects.get_or_create(
                tag=tag, content_object=page)[0]

    def create_blog_pages(self, posts, blog_index, *args, **options):
        """create Blog post entries from wordpress data"""
        for post in posts:
            post_id = post.get('ID')
            title = post.get('title')
            if title:
                new_title = self.convert_html_entities(title)
                title = new_title
            slug = post.get('slug')
            description = post.get('description')
            if description:
                description = self.convert_html_entities(description)

            body = post.get('content')
            if not "<p>" in body:
                body = linebreaks(body)

            # get image info from content and create image objects
            body = self.create_images_from_urls_in_content(body)

            # author/user data
            author = post.get('author')
            user = self.create_user(author)
            categories = post.get('terms')
            # format the date
            date = post.get('date')[:10]
            try:
                new_entry = BlogPage.objects.get(slug=slug)
                new_entry.title = title
                new_entry.body = body
                new_entry.owner = user
                new_entry.save()
            except BlogPage.DoesNotExist:
                new_entry = blog_index.add_child(instance=BlogPage(
                    title=title, slug=slug, search_description="description",
                    date=date, body=body, owner=user))
            featured_image = post.get('featured_image')
            if featured_image is not None:
                title = post['featured_image']['title']
                source = post['featured_image']['source']
                path, file_ = os.path.split(source)
                source = source.replace('stage.swoon', 'swoon')
                try:
                    remote_image = urllib.request.urlretrieve(
                        self.prepare_url(source))
                    width = 640
                    height = 290
                    header_image = Image(title=title, width=width, height=height)
                    header_image.file.save(
                        file_, File(open(remote_image[0], 'rb')))
                    header_image.save()
                except UnicodeEncodeError:
                    header_image = None
                    print('unable to set header image {}'.format(source))
            else:
                header_image = None
            new_entry.header_image = header_image
            new_entry.save()
            if categories:
                self.create_categories_and_tags(new_entry, categories)
            if self.should_import_comments:
                self.import_comments(post_id, slug)
