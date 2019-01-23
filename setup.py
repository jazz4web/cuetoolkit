from setuptools import setup, find_packages

from cuetoolkit import version

DESC = 'This is a bunch of tools for reading cuesheet files, splitting CDDA \
images and filling tracks metadata'

setup(
    name='cuetoolkit',
    version=version,
    packages=find_packages(),
    python_requires='~=3.5',
    install_requires=['mutagen>=1.36', 'chardet>=2.3.0'],
    zip_safe=False,
    scripts=['bin/cue2report',
             'bin/cue2points',
             'bin/cue2tracks',
             'bin/cue2tags',
             'bin/tags2cue'],
    author='AndreyVM',
    author_email='newbie@auriz.ru',
    description=DESC,
    license='GNU GPLv3',
    keywords='cue cdda flac image tracks vorbis opus mp3',
    url='https://gitlab.com/newbie_/cuetoolkit')
