"""
    cuetoolkit
    ~~~~~~~~~~

    A bunch of tools for reading cuesheet files, splitting CDDA images
    and filling tracks metadata.

    :copyright: (c) 2019 by AndreyVM
    :license: GNU GPLv3
"""


import importlib.util

from .exc import show_error

version = '1.0.0.pre'

if importlib.util.find_spec('chardet') is None:
    show_error('python3 module chardet is not installed')
