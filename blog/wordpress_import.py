import json
import logging
import html
import os
from io import BytesIO
from typing import List

import requests
from django.core.files import File
from django.contrib.auth import get_user_model
from wagtail.core.models import Page
from wagtail.images.models import Image

from .models import BlogPage, BlogCategory, BlogTag

User = get_user_model()

logger = logging.getLogger(__name__)


class WordpressImport:
    url = ""
    blog_index_slug = "blog"
    blog_index = None
    per_page = 50  # Number of items per page for wordpress rest api
    convert_images = False
    create_users = False  # Create users from Author data, if they don't exist
    first_page_only = False  # Only process one page. Useful in testing and previewing.

    def __init__(
        self, url: str, blog_index_slug="", convert_images=False, create_users=False
    ):
        """
        Set optional configuration

        blog_index_slug - slug of the blog index page to add blog posts to
        convert_images - Find images in imported content and convert to Wagtail Images
        """
        self.url = url
        if blog_index_slug:
            self.blog_index_slug = blog_index_slug
        self.convert_images = convert_images
        self.create_users = create_users
        self.blog_index = Page.objects.filter(slug=self.blog_index_slug).first()

    def get_headers(self):
        """ 
        Place custom headers here if needed
        """
        return {}

    def get_posts(self):
        params = {"per_page": self.per_page, "_embed": "1"}
        endpoint = self.url + "/posts"
        resp = requests.get(endpoint, headers=self.get_headers(), params=params)
        total_pages = int(resp.headers.get("X-WP-TotalPages"))
        first_page = json.loads(resp.content)

        for post in first_page:
            self.process_post(post)

        if self.first_page_only is False:
            for i in range(total_pages - 1):
                params["page"] = i + 2
                resp = requests.get(endpoint, headers=self.get_headers(), params=params)
                page = json.loads(resp.content)
                for post in page:
                    self.process_post(post)

    def process_post(self, post):
        logger.debug(post["content"]["rendered"])
        logger.info(".")
        try:
            page = BlogPage.objects.descendant_of(self.blog_index).get(
                slug=post["slug"]
            )
        except BlogPage.DoesNotExist:
            page = BlogPage(slug=post["slug"])
        page.title = self.convert_html_entities(post["title"]["rendered"])
        page.body = post["content"]["rendered"]
        if self.convert_images:
            page.body = self.create_images_from_urls_in_content(page.body)
        page.search_description = self.convert_html_entities(
            post["excerpt"]["rendered"]
        )
        page.date = post["date"][:10]
        self.set_blog_authors(page, post)
        if self.convert_images:
            self.set_featured_media(page, post)
        if page.id:
            page.save()
        else:
            self.blog_index.add_child(instance=page)
        self.set_categories(page, post)
        self.set_tags(page, post)
        page.save()  # Save is required after adding ParentalManyToManyField

    def convert_html_entities(self, text):
        """converts html symbols so they show up correctly in wagtail"""
        return html.unescape(text)

    def prepare_url(self, url):
        if url.startswith("//"):
            url = "http:{}".format(url)
        if url.startswith("/"):
            prefix_url = self.url
            if prefix_url and prefix_url.endswith("/"):
                prefix_url = prefix_url[:-1]
            url = "{}{}".format(prefix_url or "", url)
        return url

    def set_blog_authors(self, page: BlogPage, post):
        if not post["_embedded"].get("author"):
            return
        wp_author = post["_embedded"]["author"][0]
        wag_author = User.objects.filter(username=wp_author["slug"]).first()
        if wag_author:
            page.owner = wag_author
            page.author = wag_author
        elif self.create_users:
            name = wp_author["name"]
            last_name = ""
            if len(name.split()) >= 2:
                last_name = name.split()[1]
            first_name = ""
            if len(name.split()) >= 1:
                first_name = name.split()[0]
            wag_author = User.objects.create(
                username=wp_author["slug"],
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
            )
            page.owner = wag_author
            page.author = wag_author

    def set_categories(self, page: BlogPage, post):
        categories: List[int] = post["categories"]
        embed_terms = post["_embedded"].get("wp:term")
        for category in categories:
            for embed_category_list in embed_terms:
                for embed_category in embed_category_list:
                    if (
                        embed_category["id"] == category
                        and embed_category["taxonomy"] == "category"
                    ):
                        blog_category, _ = BlogCategory.objects.get_or_create(
                            slug=embed_category["slug"],
                            defaults={"name": embed_category["name"]},
                        )
                        page.blog_categories.add(blog_category)

    def set_tags(self, page: BlogPage, post):
        tags: List[int] = post["tags"]
        embed_terms = post["_embedded"].get("wp:term")
        for tag in tags:
            for embed_tag_list in embed_terms:
                for embed_tag in embed_tag_list:
                    if embed_tag["id"] == tag and embed_tag["taxonomy"] == "post_tag":
                        blog_tag, _ = BlogTag.objects.get_or_create(
                            slug=embed_tag["slug"], defaults={"name": embed_tag["name"]}
                        )
                        page.tags.add(blog_tag)

    def set_featured_media(self, page: BlogPage, post):
        featured_media_id: int = post.get("featured_media")
        if not featured_media_id:
            return
        featured_medias: list = post["_embedded"].get("wp:featuredmedia")
        if featured_medias is None:
            return
        for feature_media in featured_medias:
            if feature_media.get("id") == featured_media_id:
                source_url = feature_media["source_url"]
                try:  # Wordpress 5.3 API nests title in "rendered"
                    title = feature_media["title"]["rendered"]
                except TypeError:  # Fallback for older (or newer?) wordpress
                    title = feature_media["title"]
                details = feature_media["media_details"]
                resp = requests.get(source_url, stream=True)
                if resp.status_code != requests.codes.ok:
                    print("Unable to import " + source_url)
                    continue
                fp = BytesIO()
                fp.write(resp.content)
                image = Image(
                    title=title, width=details["width"], height=details["height"]
                )
                image.file.save(details["file"], File(fp))
                image.save()
                page.header_image = image

    def create_images_from_urls_in_content(self, body):
        """create Image objects and transfer image files to media root"""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(body, "html5lib")
        for img in soup.findAll("img"):
            if "width" in img:
                width = img["width"]
            if "height" in img:
                height = img["height"]
            else:
                width = 100
                height = 100
            _, file_name = os.path.split(img["src"])
            if not img["src"]:
                continue  # Blank image
            if img["src"].startswith("data:"):
                continue  # Embedded image
            resp = requests.get(self.prepare_url(img["src"]), stream=True)
            if resp.status_code != requests.codes.ok:
                print("Unable to import " + img["src"])
                continue
            fp = BytesIO()
            fp.write(resp.content)
            image = Image(title=file_name, width=width, height=height)
            image.file.save(file_name, File(fp))
            image.save()
            if img.has_attr("srcset"):
                img["srcset"] = ""
            try:
                new_url = image.get_rendition("original").url
                img["src"] = new_url
            except OSError:
                # Avoid https://github.com/wagtail/wagtail/issues/1326 by not importing it
                logger.warning(f"image {image} is unable to be imported")
                image.delete()
        soup.body.hidden = True
        return soup.body
