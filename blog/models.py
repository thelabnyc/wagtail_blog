from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import (
    FieldPanel, InlinePanel, MultiFieldPanel, FieldRowPanel)
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.wagtailsearch import index
from taggit.models import TaggedItemBase, Tag
from modelcluster.tags import ClusterTaggableManager
from modelcluster.fields import ParentalKey
import datetime


COMMENTS_APP = getattr(settings, 'COMMENTS_APP', None)


def get_blog_context(context):
    """ Get context data useful on all blog related pages """
    context['authors'] = get_user_model().objects.filter(
        owned_pages__live=True,
        owned_pages__content_type__model='blogpage'
    ).annotate(Count('owned_pages'))
    context['all_categories'] = BlogCategory.objects.all()
    context['root_categories'] = BlogCategory.objects.filter(parent=None)
    return context


class BlogIndexPage(Page):
    @property
    def blogs(self):
        # Get list of blog pages that are descendants of this page
        blogs = BlogPage.objects.descendant_of(self).live()
        blogs = blogs.order_by('-date')
        return blogs

    def get_context(self, request, tag=None, category=None, *args, **kwargs):
        context = super(BlogIndexPage, self).get_context(
            request, *args, **kwargs)
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
        page_size = 10
        if hasattr(settings, 'BLOG_PAGINATION_PER_PAGE'):
            page_size = settings.BLOG_PAGINATION_PER_PAGE

        if page_size is not None:
            paginator = Paginator(blogs, page_size)  # Show 10 blogs per page
            try:
                blogs = paginator.page(page)
            except PageNotAnInteger:
                blogs = paginator.page(1)
            except EmptyPage:
                blogs = paginator.page(paginator.num_pages)

        context['blogs'] = blogs
        context['category'] = category
        context['tag'] = tag
        context['COMMENTS_APP'] = COMMENTS_APP
        context = get_blog_context(context)

        return context

    class Meta:
        verbose_name = _('Blog index')
    subpage_types = ['blog.BlogPage']


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(
        max_length=80, unique=True, verbose_name=_('Category Name'))
    slug = models.SlugField(unique=True, max_length=80)
    parent = models.ForeignKey(
        'self', blank=True, null=True, related_name="children",
        help_text=_(
            'Categories, unlike tags, can have a hierarchy. You might have a '
            'Jazz category, and under that have children categories for Bebop'
            ' and Big Band. Totally optional.')
    )
    description = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = _("Blog Category")
        verbose_name_plural = _("Blog Categories")

    panels = [
        FieldPanel('name'),
        FieldPanel('parent'),
        FieldPanel('description'),
    ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.parent:
            parent = self.parent
            if self.parent == self:
                raise ValidationError('Parent category cannot be self.')
            if parent.parent and parent.parent == self:
                raise ValidationError('Cannot have circular Parents.')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(BlogCategory, self).save(*args, **kwargs)


class BlogCategoryBlogPage(models.Model):
    category = models.ForeignKey(
        BlogCategory, related_name="+", verbose_name=_('Category'))
    page = ParentalKey('BlogPage', related_name='categories')
    panels = [
        FieldPanel('category'),
    ]


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('BlogPage', related_name='tagged_items')


@register_snippet
class BlogTag(Tag):
    class Meta:
        proxy = True


class BlogPage(Page):
    body = RichTextField(verbose_name=_('body'))
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    date = models.DateField(
        _("Post date"), default=datetime.datetime.today,
        help_text=_("This date may be displayed on the blog post. It is not "
                    "used to schedule posts to go live at a later date.")
    )
    header_image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        verbose_name=_('Header image')
    )

    search_fields = Page.search_fields + (
        index.SearchField('body'),
    )
    blog_categories = models.ManyToManyField(
        BlogCategory, through=BlogCategoryBlogPage, blank=True)

    settings_panels = [
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('go_live_at'),
                FieldPanel('expire_at'),
            ], classname="label-above"),
        ], 'Scheduled publishing', classname="publishing"),
        FieldPanel('date'),
        FieldPanel('owner'),
    ]

    def get_absolute_url(self):
        return self.url

    def get_blog_index(self):
        # Find closest ancestor which is a blog index
        return self.get_ancestors().type(BlogIndexPage).last()

    def get_context(self, request, *args, **kwargs):
        context = super(BlogPage, self).get_context(request, *args, **kwargs)
        context['blogs'] = self.get_blog_index().blogindexpage.blogs
        context = get_blog_context(context)
        context['COMMENTS_APP'] = COMMENTS_APP
        return context

    class Meta:
        verbose_name = _('Blog page')
        verbose_name_plural = _('Blog pages')

    parent_page_types = ['blog.BlogIndexPage']
BlogPage._meta.get_field('owner').editable = True


BlogPage.content_panels = [
    FieldPanel('title', classname="full title"),
    MultiFieldPanel([
        FieldPanel('tags'),
        InlinePanel(BlogPage, 'categories', label=_("Categories")),
    ], heading="Tags and Categories"),
    ImageChooserPanel('header_image'),
    FieldPanel('body', classname="full"),
]
