#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages
    
import os

from PyRQ import getVersionString

setup(
    name = "PyRQ",
    version = getVersionString(),
    url = 'https://github.com/sys-git/PyRQ',
    packages = find_packages(),
    package_dir = {'PyRQ': 'PyRQ'},
    package_data={'PyRQ': ['resources/*.ui', 'resources/icons/actions/*.png', 'resources/icons/*.png']},
    include_package_data = True,
    author = "Francis Horsman",
    author_email = "francis.horsman@gmail.com",
    description = "A pure Python remote queue (RQ) implementation using the standard Queue api.",
    license = "BSD",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications',
    ]
)
