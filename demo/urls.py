from django.conf.urls import include, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import RedirectView

from wagtail.core import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.search.signal_handlers import register_signal_handlers as wagtailsearch_register_signal_handlers
from wagtail.api.v2.endpoints import PagesAPIEndpoint
from wagtail.api.v2.router import WagtailAPIRouter
import os
wagtailsearch_register_signal_handlers()

api_router = WagtailAPIRouter('wagtailapi')
api_router.register_endpoint('pages', PagesAPIEndpoint)

urlpatterns = [
    re_path(r'^blog/', include('blog.urls', namespace="blog")),
    re_path(r'^django-admin/', admin.site.urls),
    re_path(r'^admin/', include(wagtailadmin_urls)),
    re_path(r'^comments/', include('django_comments_xtd.urls')),
    re_path(r'^api/v2/', api_router.urls),
    re_path(r'', include(wagtail_urls)),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL + 'images/', document_root=os.path.join(settings.MEDIA_ROOT, 'images'))
    urlpatterns += [
        re_path(r'^favicon\.ico$', RedirectView.as_view(url=settings.STATIC_URL + 'demo/images/favicon.ico'))
    ]
