import json
import logging
import html
import os
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from django.core.files import File
from wagtail.core.models import Page
from wagtail.images.models import Image

from .models import BlogPage


class WordpressImport():
    url = ""
    blog_index_slug = 'blog'
    blog_index = None
    per_page = 50  # Number of items per page for wordpress rest api
    convert_images = False

    def __init__(self, url: str, blog_index_slug='', convert_images=True):
        """
        Set optional configuration

        blog_index_slug - slug of the blog index page to add blog posts to
        convert_images - Find images in imported content and convert to Wagtail Images
        """
        self.url = url
        if blog_index_slug:
            self.blog_index_slug = blog_index_slug
        self.convert_images = convert_images
        self.blog_index = Page.objects.filter(slug=self.blog_index_slug).first()

    def get_headers(self):
        """ Place custom headers here if needed """
        return {}

    def get_posts(self):
        params = {
            "per_page": self.per_page
        }
        endpoint = self.url + "/posts"
        resp = requests.get(endpoint, headers=self.get_headers(), params=params)
        total_pages = int(resp.headers.get('X-WP-TotalPages'))
        first_page = json.loads(resp.content)

        for post in first_page:
            self.process_post(post)

        # for i in range(total_pages - 1):
        #     params['page'] = i + 2
        #     resp = requests.get(endpoint, headers=self.get_headers(), params=params)
        #     page = json.loads(resp.content)
        #     for post in page:
        #         self.process_post(post)

    def process_post(self, post):
        logging.debug(post['content']['rendered'])
        logging.info('.')
        try:
            page = BlogPage.objects.descendant_of(self.blog_index).get(slug=post['slug'])
        except BlogPage.DoesNotExist:
            page = BlogPage(slug=post['slug'])
        page.title = self.convert_html_entities(post['title']['rendered'])
        page.body = post['content']['rendered']
        if self.convert_images:
            page.body = self.create_images_from_urls_in_content(page.body)
        page.search_description = self.convert_html_entities(post['excerpt']['rendered'])
        page.date = post['date'][:10]
        if page.id:
            page.save()
        else:
            self.blog_index.add_child(instance=page)

    def convert_html_entities(self, text):
        """converts html symbols so they show up correctly in wagtail"""
        return html.unescape(text)

    def prepare_url(self, url):
        if url.startswith('//'):
            url = 'http:{}'.format(url)
        if url.startswith('/'):
            prefix_url = self.url
            if prefix_url and prefix_url.endswith('/'):
                prefix_url = prefix_url[:-1]
            url = '{}{}'.format(prefix_url or "", url)
        return url

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
            _, file_name = os.path.split(img['src'])
            if not img['src']:
                continue  # Blank image
            if img['src'].startswith('data:'):
                continue # Embedded image
            resp = requests.get(self.prepare_url(img['src']), stream=True)
            if resp.status_code != requests.codes.ok:
                print("Unable to import " + img['src'])
                continue
            fp = BytesIO()
            fp.write(resp.content)
            image = Image(title=file_name, width=width, height=height)
            image.file.save(file_name, File(fp))
            image.save()
            new_url = image.file.url
            body = body.replace(old_url, new_url)
            body = self.convert_html_entities(body)
        return body
        