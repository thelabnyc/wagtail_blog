from django.core.management.base import BaseCommand
from blog.wordpress_import import WordpressImport


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "blog_index", help="Title of blog index page to attach blogs"
        )
        parser.add_argument("--url", help="Base url of wordpress instance")
        parser.add_argument(
            "--convert-images",
            default=False,
            type=bool,
            help="Find and convert images to Wagtail Images",
        )
        parser.add_argument(
            "--create-users",
            default=False,
            type=bool,
            help="Create users out of found Authors",
        )

    def handle(self, *args, **options):
        url = options.get("url")
        url = url.rstrip("/")
        wordpress_import = WordpressImport(
            url,
            convert_images=options.get("convert_images"),
            create_users=options.get("create_users"),
        )
        wordpress_import.get_posts()
