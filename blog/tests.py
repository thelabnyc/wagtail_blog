from django.test import TestCase
import json
from django_comments.models import Comment
from django_comments_xtd.models import XtdComment
from wagtail.wagtailcore.models import Page
from django.contrib.auth.models import User
from .models import BlogPage, BlogTag, BlogPageTag, BlogIndexPage, BlogCategory, BlogCategoryBlogPage
from .management.commands.wordpress_to_wagtail import Command


class BlogTests(TestCase):
    def setUp(self):
        home = Page.objects.get(slug='home')
        self.user = User.objects.create_user('test', 'test@test.test', 'pass')
        self.blog_index = home.add_child(instance=BlogIndexPage(
            title='Blog Index', slug='blog', search_description="x",
            owner=self.user))

    def test_import(self):
        """
        Tests migrate_wordpress command - 
        	the command should do the following:
        	1. create BlogPage objects from a given BlogIndex
        	2. create category and tag objects as BlogCategory, 
        	   BlogTag, BlogPageBlogCategory and BlogPageTag objects
        The test imports from test-data.json which includes one wordpress blog post with 11 tags and 2 categories
        """
        command = Command()
        command.username = None
        command.password = None
        with open('test-data.json') as test_json:
            posts = json.load(test_json)
        command.create_blog_pages(posts, self.blog_index)
        self.assertEquals(Page.objects.all().count(), 4)
        self.assertEquals(BlogPage.objects.all().count(), 1)
        page = BlogPage.objects.get()
        self.assertEqual(page.title, "My wordpress title")
        self.assertInHTML("<strong>Bold here</strong>", page.body)
        self.assertTrue("media" in page.body)
        self.assertEqual(page.categories.count(), 2)
        self.assertEqual(page.tags.count(), 11)
        self.assertEqual(page.owner.id, 2)
        self.assertEqual(BlogCategory.objects.all().count(), 2)
        self.assertEqual(BlogTag.objects.all().count(), 11)
        self.assertEqual(BlogCategoryBlogPage.objects.all().count(), 2)
        self.assertEqual(BlogPageTag.objects.all().count(), 11)
        parent_category = BlogCategory.objects.get(slug="writing-wisdom")
        child_category = BlogCategory.objects.get(slug="swoon-reads")
        self.assertEqual(child_category.parent, parent_category)
        self.assertEqual(child_category.slug, "swoon-reads")
        self.assertEqual(parent_category.slug, "writing-wisdom")
        command.import_comments(10376, "collaborative-editing-further-evidence-that-holly-and-lauren-are-probably-crazy")        
        comments = XtdComment.objects.all()
        self.assertEqual(comments.count(), 22)        
        parent_comment = XtdComment.objects.filter(thread_id=0)[0]
        child_comment = XtdComment.objects.filter(thread_id=1)[0]
        #test to make sure nested comments are attached to the same blog post
        self.assertEqual(parent_comment.content_type, child_comment.content_type)
        
