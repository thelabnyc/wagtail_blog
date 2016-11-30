from setuptools import setup, find_packages

setup(
    name = "wagtail-blog",
    version = "1.6.9",
    author = "David Burke",
    author_email = "david@thelabnyc.com",
    description = ("A wordpress like blog app implemented in wagtail"),
    license = "Apache License",
    keywords = "django wagtail blog",
    url = "https://github.com/thelabnyc/wagtail_blog",
    packages=find_packages('.', exclude=('tests', 'demo')),
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Intended Audience :: Developers',
        "License :: OSI Approved :: Apache Software License",
    ],
    install_requires=[
        'wagtail>=1.0.0',
        'requests',
        'lxml'
    ]
)
