# 2.3.0

- Wordpress API importer works better with --convert-images by removing wordpress srcset attribute and other minor fixes
- Categories now uses ParentalManyToManyField instead of ManyToManyField which may be required for newer versions django-modelcluster and should support drafts better

# 2.2.0

- New Wordpress API importer (Old ones still exist but haven't been updated in years)
- Switch to poetry to dependencies management

# 2.1.0

- Update Django version to 2.1 on demo app
- Added abstract base models for all models. Shouldn't change or break anything.
- Removed some unneeded python 2.x syntax
- Added publication date to atom feed

# 2.0.2

- Fixed slug generation on category

# 2.0.1

- Set requires wagtail>=2.0.0
- Support for custom image fields

# 2.0.0

2.0 contains a breaking change to support Wagtail 2.0. Please use 1.7.x if you need to support Python 2 or Wagtail 1.x.

- Updated imports to use new wagtail 2.0 modules
- Removed python 2 support

# 1.7.0

- Added full django 1.11 and wagtail 1.13 support
- Notice of intent to remove python 2 support (no changes have been made yet and python 2 will still work at this time)
- Moved to Gitlab (because freedom!) and Gitlab CI for testing
