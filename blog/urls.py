from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(r'^tag/(?P<tag>[-\w]+)/', views.tag_view, name="tag"),
    url(r'^category/(?P<category>[-\w]+)/feed/$', views.LatestCategoryFeed(), name="category_feed"),
    url(r'^category/(?P<category>[-\w]+)/', views.category_view, name="category"),
    url(r'^author/(?P<author>[-\w]+)/', views.author_view, name="author"),
)
