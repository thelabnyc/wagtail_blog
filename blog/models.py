from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.db import models
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailcore.fields import RichTextField
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import FieldPanel, InlinePanel
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.wagtailsearch import index
from taggit.models import TaggedItemBase
from modelcluster.tags import ClusterTaggableManager
from modelcluster.fields import ParentalKey


COMMENTS_APP = getattr(settings, 'COMMENTS_APP', None)


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
        paginator = Paginator(blogs, 10)  # Show 10 blogs per page
        try:
            blogs = paginator.page(page)
        except PageNotAnInteger:
            blogs = paginator.page(1)
        except EmptyPage:
            blogs = paginator.page(paginator.num_pages)

        context['blogs'] = blogs
        context['category'] = category
        context['all_categories'] = BlogCategory.objects.all()
        context['tag'] = tag
        context['COMMENTS_APP'] = COMMENTS_APP

        return context

    class Meta:
        verbose_name = _('Blog index')


@register_snippet
class BlogCategory(models.Model):
    name = models.CharField(
        max_length=80, unique=True, verbose_name=_('Category Name'))
    slug = models.SlugField(unique=True, max_length=80)

    class Meta:
        ordering = ['name']
        verbose_name = _("Blog Category")
        verbose_name_plural = _("Blog Categories")
    
    panels = [
        FieldPanel('name')
    ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super(BlogCategory, self).save(*args, **kwargs)


class BlogCategoryBlogPage(models.Model):
    category = models.ForeignKey(BlogCategory, related_name="+", verbose_name=_('Category'))
    page = ParentalKey('BlogPage', related_name='categories')
    panels = [
        FieldPanel('category'),
    ]


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey('BlogPage', related_name='tagged_items')


class BlogPage(Page):
    body = RichTextField(verbose_name=_('body'))
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    date = models.DateField(_("Post date"))
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

    def get_absolute_url(self):
        return self.url

    def get_blog_index(self):
        # Find closest ancestor which is a blog index
        return self.get_ancestors().type(BlogIndexPage).last()

    def get_context(self, request, *args, **kwargs):
        context = super(BlogPage, self).get_context(request, *args, **kwargs)
        context['all_categories'] = BlogCategory.objects.all()
        context['blogs'] = self.get_blog_index().blogindexpage.blogs
        context['COMMENTS_APP'] = COMMENTS_APP
        return context

    class Meta:
        verbose_name = _('Blog page')
        verbose_name_plural = _('Blog pages')


BlogPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('date'),
    FieldPanel('tags'),
    ImageChooserPanel('header_image'),
    InlinePanel(BlogPage, 'categories', label=_("Categories")),
    FieldPanel('body', classname="full"),
]
