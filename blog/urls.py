from django.conf.urls import patterns, url
from . import views


urlpatterns = patterns('',
    url(r'^tag/(?P<tag>[-\w]+)/', views.tag_view),
    url(r'^category/(?P<category>[-\w]+)/feed/$', views.LatestCategoryFeed()),
    url(r'^category/(?P<category>[-\w]+)/', views.category_view),
)
