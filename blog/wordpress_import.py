import requests
import json
import logging
import html

from wagtail.core.models import Page

from .models import BlogPage


class WordpressImport():
    url = ""
    blog_index_slug = 'blog'
    blog_index = None

    def __init__(self, url: str, blog_index_slug = ''):
        self.url = url
        if blog_index_slug:
            self.blog_index_slug = blog_index_slug
        self.blog_index = Page.objects.filter(slug=self.blog_index_slug).first()

    def get_headers(self):
        """ Place custom headers here if needed """
        return {}

    def get_posts(self):
        params = {
            "per_page": 50
        }
        endpoint = self.url + "/posts"
        resp = requests.get(endpoint, headers=self.get_headers(), params=params)
        total_pages = int(resp.headers.get('X-WP-TotalPages'))
        first_page = json.loads(resp.content)

        for post in first_page:
            self.process_post(post)

        for i in range(total_pages - 1):
            params['page'] = i + 2
            resp = requests.get(endpoint, headers=self.get_headers(), params=params)
            page = json.loads(resp.content)
            for post in page:
                self.process_post(post)

        pass

    def process_post(self, post):
        logging.debug(post['content']['rendered'])
        logging.info('.')
        try:
            page = BlogPage.objects.descendant_of(self.blog_index).get(slug=post['slug'])
        except BlogPage.DoesNotExist:
            page = BlogPage(slug=post['slug'])
        page.title = html.unescape(post['title']['rendered'])
        page.body = post['content']['rendered']
        page.search_description = html.unescape(post['excerpt']['rendered'])
        page.date = post['date'][:10]
        if page.id:
            page.save()
        else:
            self.blog_index.add_child(instance=page)
        