from django.contrib.syndication.views import Feed
from .models import BlogIndexPage, BlogPage, BlogCategory
from django.shortcuts import get_object_or_404


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
    title = "Blog"
    link = "/blog/"
    description = "A Blog"

    def items(self):
        return BlogPage.objects.order_by('-date')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body


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
