import doctest
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django_comments_xtd.models import XtdComment

from wagtail.wagtailcore.models import Page

from .models import (BlogPage, BlogTag, BlogPageTag, BlogIndexPage,
                     BlogCategory, BlogCategoryBlogPage)
from .management.commands.wordpress_to_wagtail import Command
from . import wp_xml_parser

def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(wp_xml_parser))
    return tests

class BlogTests(TestCase):
    def setUp(self):
        home = Page.objects.get(slug='home')
        self.user = User.objects.create_user('test', 'test@test.test', 'pass')
        self.xml_path = "example_export.xml"
        self.blog_index = home.add_child(instance=BlogIndexPage(
            title='Blog Index', slug='blog', search_description="x",
            owner=self.user))

    def test_index(self):
        url = self.blog_index.url
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

        blog_page = self.blog_index.add_child(instance=BlogPage(
            title='Blog Page', slug='blog_page1', search_description="x",
            owner=self.user))
        url = blog_page.url
        res = self.client.get(url)
        self.assertContains(res, "Blog Page")

    def test_latest_entries_feed(self):
        self.blog_index.add_child(instance=BlogPage(
                                  title='Blog Page',
                                  slug='blog_page1',
                                  search_description="x",
                                  owner=self.user))
        res = self.client.get("{0}{1}/rss/".format(self.blog_index.url,
                                                   self.blog_index.slug))
        self.assertContains(res, "Blog Page")
        self.assertContains(res, '<rss')
        self.assertContains(res, 'version="2.0"')
        self.assertContains(res, '</rss>')

    def test_latest_entries_feed_atom(self):
        self.blog_index.add_child(instance=BlogPage(
                                  title='Blog Page',
                                  slug='blog_page1',
                                  search_description="x",
                                  owner=self.user))
        res = self.client.get("{0}{1}/atom/".format(self.blog_index.url,
                                                    self.blog_index.slug))
        self.assertContains(res, "Blog Page")
        self.assertContains(res, '<feed')
        self.assertContains(res, 'xmlns="http://'
                                 'www.w3.org/2005/Atom"')
        self.assertContains(res, '</feed>')

    def test_import_url(self):
        """
        Tests migrate_wordpress command -
            the command should do the following:
            1. create BlogPage objects from a given BlogIndex
            2. create category and tag objects as BlogCategory,
               BlogTag, BlogPageBlogCategory and BlogPageTag objects
        The test imports from test-data.json which includes one wordpress blog
        post with 11 tags and 2 categories
        """
        command = Command()
        command.username = None
        command.password = None
        command.should_import_comments = True
        command.url = 'just_testing'
        with open('test-data.json') as test_json:
            posts = json.load(test_json)
        command.create_blog_pages(posts, self.blog_index)
        self.assertEquals(Page.objects.all().count(), 4)
        self.assertEquals(BlogPage.objects.all().count(), 1)
        page = BlogPage.objects.get()
        self.assertEqual(page.title, "My wordpress title")
        self.assertInHTML("<strong>Bold here</strong>", page.body)
        self.assertEqual(page.categories.count(), 2)
        self.assertEqual(page.tags.count(), 11)
        self.assertEqual(page.owner.id, 2)
        self.assertEqual(BlogCategory.objects.all().count(), 2)
        self.assertEqual(BlogTag.objects.all().count(), 11)
        self.assertEqual(BlogCategoryBlogPage.objects.all().count(), 2)
        self.assertEqual(BlogPageTag.objects.all().count(), 11)
        parent_category = BlogCategory.objects.get(slug="writing-wisdom")
        child_category = BlogCategory.objects.get(slug="swoon-reads")
        self.assertTrue(child_category.parent is not None)
        self.assertEqual(child_category.parent, parent_category)
        self.assertEqual(child_category.slug, "swoon-reads")
        self.assertEqual(parent_category.slug, "writing-wisdom")
        comments = XtdComment.objects.all()
        self.assertEqual(comments.count(), 2)
        parent_comment = XtdComment.objects.get(level=0)
        child_comment = XtdComment.objects.get(level=1)
        self.assertEqual(parent_comment.id, child_comment.parent_id)

    def test_import_xml(self):
        """
        Tests migrate_wordpress command -
            the command should do the following:
            1. create BlogPage objects from a given BlogIndex
            2. create category and tag objects as BlogCategory,
               BlogTag, BlogPageBlogCategory and BlogPageTag objects
        The test imports from example_export.xml which includes a wordpress blog
        """
        command = Command()
        # command.username = None
        # command.password = None
        # command.should_import_comments = True
        command.handle(xml=self.xml_path, blog_index="blog")
        self.assertEquals(Page.objects.all().count(), 18)
        self.assertEquals(BlogPage.objects.all().count(), 15)
        page = BlogPage.objects.filter(slug='40-under-40-katz').get()
        self.assertEqual(page.title, "40 Under 40 Katz")
        self.assertInHTML("<strong>should</strong>", page.body)
        # print(page.title, page.categories)
        self.assertEqual(page.categories.count(), 2)
        self.assertEqual(page.tags.count(), 1)
        self.assertEqual(page.owner.id, 2)
        self.assertEqual(BlogCategory.objects.all().count(), 2)
        self.assertEqual(BlogTag.objects.all().count(), 1)
        self.assertEqual(BlogCategoryBlogPage.objects.all().count(), 2)
        self.assertEqual(BlogPageTag.objects.all().count(), 1)
        parent_category = BlogCategory.objects.get(slug="marketing-2")
        child_category = BlogCategory.objects.get(slug="cheat-sheets")
        self.assertTrue(child_category.parent is not None)
        self.assertEqual(child_category.parent, parent_category)
        self.assertEqual(child_category.slug, "cheat-sheets")
        self.assertEqual(parent_category.slug, "marketing-2")

