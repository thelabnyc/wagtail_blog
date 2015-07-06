from django.test import TestCase
import json
from wagtail.wagtailcore.models import Page
from django.contrib.auth.models import User
from .models import BlogPage, BlogTag, BlogPageTag, BlogIndexPage,
                         BlogCategory, BlogCategoryBlogPage
from .management.commands.wordpress_to_wagtail import Command


class BlogTests(TestCase):
    def setUp(self):
        home = Page.objects.get(slug='home')
        self.user = User.objects.create_user('test', 'test@test.test', 'pass')
        self.blog_index = home.add_child(instance=BlogIndexPage(
            title='Blog Index', slug='blog', search_description="x",
            owner=self.user))
        self.blog_page = self.blog_index.add_child(instance=BlogPage(title="blog entry", 
                         slug="blog-entry", search_description="description", body="some content goes here",
                         owner=self.user, date='10:10:2010'))
        self.parent_blog_category = BlogCategory.objects.create(name="first category", slug="first-category")
        self.child_blog_category = BlogCategory.objects.create(name="second category", slug="second-category", parent=self.parent_blog_category)
        self.first_tag = BlogTag.objects.create(name="first tag", slug="first-tag")
        self.second_tag = BlogTag.objects.create(name="second tag", slug="second-tag")

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
        self.assertEqual(BlogPageBlogCategory.objects.all().count(), 2)
        self.assertEqual(BlogPageTag.objects.all().count(), 11)
        parent_category = BlogCategory.objects.get(slug="writing-wisdom")
        child_category = BlogCategory.objects.get(slug="swoon-reads")
        self.assertEqual(child_category.parent, parent_category)
        self.assertEqual(child_category.slug, "swoon-reads")
        self.assertEqual(parent_category.slug, "writing-wisdom")        
        
        
    def test_blog_categories_and_tags(self):
        """Test to make sure that categories and tags are created correctly, 
            and that a parent category is set correctly when it exists.
            Tests to make sure that when there are categories and tags for a given blog post,
            that BlogPageTag and BlogPageBlogCategory objects are created for each combination of tags/categories and posts.
            
            This test does not test any of the imports from a wordpress site, it just tests
            whether or not the objects are being created and uses 
        
        """
        self.assertEqual(BlogCategory.objects.all().count(), 2)
        blog_category_child = BlogCategory.objects.get(name="second category")
        blog_category_parent = BlogCategory.objects.get(name="first category")
        self.assertEqual(blog_category_child.parent, blog_category_parent)
        self.assertFalse(blog_category_child.parent, None)
        page = self.blog_page
        page_category = BlogPageBlogCategory.objects.create(page=page, category=blog_category_child)
        second_category = BlogPageBlogCategory.objects.create(page=page, category=blog_category_parent)
        self.assertEqual(page_category.page, page)
        self.assertEqual(second_category.page, page)
        page_tag = BlogPageTag.objects.create(tag = self.second_tag, content_object=page)
        second_page_tag = BlogPageTag.objects.create(tag=self.first_tag, content_object=page)
        self.assertEqual(BlogPageBlogCategory.objects.all().count(), 2)
        self.assertEqual(BlogPageTag.objects.all().count(), 2)
        
        
