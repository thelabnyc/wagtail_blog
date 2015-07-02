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
            owner=self.user
        ))
        self.parent_blog_category = BlogCategory.objects.create(name="first category", slug="first-category")
        self.child_blog_category = BlogCategory.objects.create(name="second category", slug="second-category", parent=self.parent_blog_category)
        self.first_tag = BlogTag.objects.create(name="first tag", slug="first-tag")
        self.second_tag = BlogTag.objects.create(name="second tag", slug="second-tag")

    def test_import(self):
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
        
    def test_blog_categories_and_tags(self):
        self.assertEqual(BlogCategory.objects.all().count(), 2)
        blog_category_child = BlogCategory.objects.get(name="second category")
        blog_category_parent = BlogCategory.objects.get(name="first category")
        self.assertEqual(blog_category_child.parent, blog_category_parent)
        self.assertFalse(blog_category_child.parent, None)
        page = BlogPage.objects.get()
        page_category = BlogPageBlogCategory.objects.create(page=page, category=blog_category_child)
        second_category = BlogPageBlogCategory.objects.create(page=page, category=blog_category_parent)
        self.assertEqual(page_category.page, page)
        self.assertEqual(second_category.page, page)
        page_tag = BlogPageTag.objects.create(tag = self.second_tag, content_object=page)
        second_page_tag = BlogPageTag.objects.create(tag=self.first_tag, content_object=page)
        self.assertEqual(BlogPageBlogCategory.objects.all().count(), 2)
        self.assertEqual(BlogPageTag.objects.all().count(), 2)
        
        
