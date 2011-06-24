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
    download_url='https://github.com/gdoermann/django-limbo/raw/master/django-limbo-1.7.0.tar.gz',
    license='https://github.com/gdoermann/django-limbo/blob/master/MIT-LICENSE.txt',
    platform=['Any'],
    packages=['limbo',],
    requires=['django', ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Software Development :: Libraries :: Python Modules',
   ],
     )
