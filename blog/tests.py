from django.test import TestCase
import requests
from bs4 import BeautifulSoup

class BlogTests(TestCase):
    def setUp(self):
        self.blog_index = BlogIndex.objects.get(title="myindex")
        self.author = {} #json string
        fake_content_blurb = {} #json string
        self.soup = BeautifulSoup(fake_content_blurb)
        print(data_url)


    def test_posts_link(self, url)
        pass

    def test_create_images_from_content(self):
        pass

    def test_create_users_from_author_data(self):
        pass

    def test_create_blog_pages(self):
        pass

    def test_create_blog_tags_and_categories(self):
        pass
