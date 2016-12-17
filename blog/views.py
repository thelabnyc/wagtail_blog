from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from .models import BlogIndexPage, BlogPage, BlogCategory
from django.shortcuts import get_object_or_404
from django.conf import settings


def tag_view(request, tag):
    index = BlogIndexPage.objects.first()
    return index.serve(request, tag=tag)


def category_view(request, category):
    index = BlogIndexPage.objects.first()
    return index.serve(request, category=category)


def author_view(request, author):
    index = BlogIndexPage.objects.first()
    return index.serve(request, author=author)


class LatestEntriesFeed(Feed):
    '''
    If a URL ends with "rss" try to find a matching BlogIndexPage
    and return its items.
    '''

    def get_object(self, request, blog_slug):
        return get_object_or_404(BlogIndexPage, slug=blog_slug)

    def title(self, blog):
        if blog.seo_title:
            return blog.seo_title
        return blog.title

    def link(self, blog):
        return blog.full_url

    def description(self, blog):
        return blog.search_description

    def items(self, blog):
        num = getattr(settings, 'BLOG_PAGINATION_PER_PAGE', 10)
        return blog.get_descendants().order_by('-first_published_at')[:num]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.specific.body

    def item_link(self, item):
        return item.full_url


class LatestEntriesFeedAtom(LatestEntriesFeed):
    feed_type = Atom1Feed


class LatestCategoryFeed(Feed):
    description = "A Blog"

    def title(self, category):
        return "Blog: " + category.name

    def link(self, category):
        return "/blog/category/" + category.slug

    def get_object(self, request, category):
        return get_object_or_404(BlogCategory, slug=category)

    def items(self, obj):
        return BlogPage.objects.filter(
            categories__category=obj).order_by('-date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body
