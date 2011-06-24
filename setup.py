#!/usr/bin/env python
__author__ = 'gdoermann'

from distutils.core import setup

setup(
    name='Django Limbo',
    version='1.7.0',
    url='https://github.com/gdoermann/django-limbo',
    author='Gregory Doermann',
    author_email='dev@doermann.me',
    summary='A bunch of django libraries that hang in limbo...',
    description="""
    This is a long list of libraries I have used in almost all of my projects.
    This also includes altered code from django snippets and code I have copied directly from others.
    """,
    download_url='https://github.com/gdoermann/django-limbo/tarball/master',
    license='https://github.com/gdoermann/django-limbo/blob/master/MIT-LICENSE.txt',
    platform=['Any'],
    packages=['limbo',],
    requires=['django', ]
     )
