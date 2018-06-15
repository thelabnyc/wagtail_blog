import doctest
import json

from django.core.management import call_command
from django.contrib.auth.models import User
from django.test import TestCase
from django_comments_xtd.models import XtdComment

from wagtail.core.models import Page

from .models import (BlogPage, BlogTag, BlogPageTag, BlogIndexPage,
                     BlogCategory, BlogCategoryBlogPage)
from .management.commands.wordpress_to_wagtail import Command
from . import wp_xml_parser


def load_tests(loader, tests, ignore):
    tests.addTests(doctest.DocTestSuite(wp_xml_parser))
    return tests
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group


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

    def test_author(self):
        # make super to access admin
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.client.login(username='test', password='pass'))
        # make an is_staff admin
        staff_user = User.objects.create_user('mr.staff', 'staff@test.test', 'pass')
        staff_user.is_staff = True
        staff_user.save()
        # make some groups
        bloggers = 'Bloggers'
        Group.objects.create(name=bloggers)
        others = 'Others'
        Group.objects.create(name=others)
        # make a non-admin Blogger author
        author_user = User.objects.create_user('mr.author', 'author@test.test', 'pass')
        author_user.groups.add(Group.objects.get(name=bloggers))
        author_user.save()
        # make a blog page
        blog_page = self.blog_index.add_child(instance=BlogPage(
            title='Blog Page', slug='blog_page1', search_description="x",
            owner=self.user))

        with self.settings(BLOG_LIMIT_AUTHOR_CHOICES_GROUP=None, BLOG_LIMIT_AUTHOR_CHOICES_ADMIN=False):
            response = self.client.get(
                reverse('wagtailadmin_pages:edit', args=(blog_page.id, )),
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'mr.staff')
            self.assertNotContains(response, 'mr.author')

        with self.settings(BLOG_LIMIT_AUTHOR_CHOICES_GROUP=bloggers, BLOG_LIMIT_AUTHOR_CHOICES_ADMIN=False):
            response = self.client.get(
                reverse('wagtailadmin_pages:edit', args=(blog_page.id, )),
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'mr.staff')
            self.assertContains(response, 'mr.author')

        with self.settings(BLOG_LIMIT_AUTHOR_CHOICES_GROUP=bloggers, BLOG_LIMIT_AUTHOR_CHOICES_ADMIN=True):
            response = self.client.get(
                reverse('wagtailadmin_pages:edit', args=(blog_page.id, )),
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'mr.staff')
            self.assertContains(response, 'mr.author')

        with self.settings(BLOG_LIMIT_AUTHOR_CHOICES_GROUP=[bloggers, others], BLOG_LIMIT_AUTHOR_CHOICES_ADMIN=False):
            response = self.client.get(
                reverse('wagtailadmin_pages:edit', args=(blog_page.id, )),
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'mr.staff')
            self.assertContains(response, 'mr.author')

        with self.settings(BLOG_LIMIT_AUTHOR_CHOICES_GROUP=[bloggers, others], BLOG_LIMIT_AUTHOR_CHOICES_ADMIN=True):
            response = self.client.get(
                reverse('wagtailadmin_pages:edit', args=(blog_page.id, )),
                follow=True
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'mr.staff')
            self.assertContains(response, 'mr.author')

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
        command.handle(xml=self.xml_path, blog_index="blog")
        self.assertEquals(Page.objects.all().count(), 6)
        self.assertEquals(BlogPage.objects.all().count(), 3)
        page = BlogPage.objects.filter(slug='10-things-super-successful-people-do-during-lunch').get()
        self.assertEqual(page.title, "10 Things Super Successful People Do During Lunch")
        self.assertEqual(page.body, "<p>Before you spend another lunch scarfing down food at your desk with your eyes glued to your computer screen, here's some food for thought.</p>")
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

        # Assert that <p> tags were added to the post that didn't contain them         
        page = BlogPage.objects.filter(slug='asa-releases-2013-economic-analysis-of-staffing-industry-trends').get()
        self.assertEqual(page.body, "<p>The American Staffing Association has released its 2013 economic analysis,\"Navigating the 1% Economy.\" Written by ASA chief operating officer Steven P. Berchem, CSP, the report takes an in-depth look at recent staffing employment trends and what these suggest about the current economic environment and future labor market conditions.</p>")


    def test_import_xml_comments(self):
        """
        Comment data in XML should be inserted and threaded correctly
        """
        call_command(
            "wordpress_to_wagtail",
            "blog",
            xml=self.xml_path,
            import_comments=True
        )
        comments = XtdComment.objects.all()
        self.assertEqual(comments.count(), 2)
        parent_comment = XtdComment.objects.get(level=0)
        child_comment = XtdComment.objects.get(level=1)
        self.assertEqual(parent_comment.id, child_comment.parent_id)

    def test_unique_category_slug(self):
        """ Ensure unique slugs are generated without erroring """
        BlogCategory.objects.create(name="one")
        BlogCategory.objects.create(name="one#")
        BlogCategory.objects.create(name="one!")
