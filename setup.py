from setuptools import setup, find_packages

setup(
    name = "wagtail-blog",
    version = "2.0.2",
    author = "David Burke",
    author_email = "david@thelabnyc.com",
    description = ("A wordpress like blog app implemented in wagtail"),
    license = "Apache License",
    keywords = "django wagtail blog",
    url = "https://gitlab.com/thelabnyc/wagtail_blog",
    packages=find_packages('.', exclude=('tests', 'demo')),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Wagtail',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=[
        'wagtail>=2.0.0',
        'requests',
        'lxml'
    ]
)
