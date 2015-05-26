from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from django.conf import settings
import urllib.request 
import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from blog.models import BlogPage, BlogTag, BlogPageTag, BlogIndexPage, BlogCategory, BlogCategoryBlogPage
from django.contrib.auth.models import User
from wagtail.wagtailimages.models import Image
from demo import settings


class Command(BaseCommand):
	

    def handle(self, *args, **options):
        pass
