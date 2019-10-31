from django.core.management.base import BaseCommand
from blog.wordpress_import import WordpressImport


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('blog_index', help="Title of blog index page to attach blogs")
        parser.add_argument('--url',
                            default=False,
                            help="Base url of wordpress instance")

    def handle(self, *args, **options):
        url = options.get('url')
        wordpress_import = WordpressImport(url)
        wordpress_import.get_posts()
