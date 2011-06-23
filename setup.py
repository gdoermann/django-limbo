#!/usr/bin/env python
__author__ = 'gdoermann'

from distutils.core import setup

setup(name='Django Limbo',
      version='1.7.0',
      description='A bunch of django libraries that hang in limbo...',
      author='Gregory Doermann',
      author_email='dev@doermann.me',
      url='https://github.com/gdoermann/django-limbo',
      packages=['limbo',],
      requires=['django', ]
     )
