from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import models
from django.shortcuts import get_object_or_404, render
from django.template.defaultfilters import slugify
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page, Orderable
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsnippets.models import register_snippet
from taggit.models import TaggedItemBase
from modelcluster.tags import ClusterTaggableManager
from modelcluster.fields import ParentalKey


class BlogIndexPage(Page):
    @property
    def blogs(self):
        # Get list of blog pages that are descendants of this page
        blogs = BlogPage.objects.filter(
            live=True,
            path__startswith=self.path
        )
        blogs = blogs.order_by('-date')
        return blogs

    def serve(self, request, tag=None, category=None):
        blogs = self.blogs

        if tag is None:
            tag = request.GET.get('tag')
        if tag:
            blogs = blogs.filter(tags__slug=tag)
        if category is None:  # Not coming from category_view in views.py
            if request.GET.get('category'):
                category = get_object_or_404(
                    BlogCategory, slug=request.GET.get('category'))
        if category:
            if not request.GET.get('category'):
                category = get_object_or_404(BlogCategory, slug=category)
            blogs = blogs.filter(categories__category__name=category)

        # Pagination
        page = request.GET.get('page')
        paginator = Paginator(blogs, 10)  # Show 10 blogs per page
        try:
            blogs = paginator.page(page)
        except PageNotAnInteger:
            blogs = paginator.page(1)
        except EmptyPage:
            blogs = paginator.page(paginator.num_pages)

        return render(request, self.template, {
            'self': self,
            'blogs': blogs,
            'category': category,
            'tag': tag,
        })


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(
        max_length=80, unique=True, verbose_name='Category Name')
    slug = models.SlugField(unique=True, max_length=80)

    class Meta:
        ordering = ['name']
        verbose_name_plural = "Blog Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(BlogCategory, self).save(*args, **kwargs)


class BlogCategoryBlogPage(Orderable, models.Model):
    category = models.ForeignKey(BlogCategory, related_name="+")
    page = ParentalKey('BlogPage', related_name='categories')
    panels = [
        FieldPanel('category'),
    ]


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('BlogPage', related_name='tagged_items')


class BlogPage(Page):
    body = RichTextField()
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    date = models.DateField("Post date")
    header_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    indexed_fields = ('body', )

    @property
    def blog_index(self):
        # Find closest ancestor which is a blog index
        return self.get_ancestors().type(BlogIndexPage).last()

    def get_blog_index(self):
        blog_index_page = None
        for index_page in BlogIndexPage.objects.all():
            if self in index_page.blogs:
                blog_index_page = index_page
                return blog_index_page
        return blog_index_page

BlogPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('date'),
    FieldPanel('tags'),
    ImageChooserPanel('header_image'),
    InlinePanel(BlogPage, 'categories', label="Categories"),
    FieldPanel('body', classname="full"),
]
