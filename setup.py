from setuptools import setup, find_packages

from cuetoolkit import version

DESC = 'This is a bunch of tools for reading cuesheet files, splitting CDDA \
images and filling tracks metadata'

setup(
    name='cuetoolkit',
    version=version,
    packages=find_packages(),
    python_requires='~=3.7',
    install_requires=['mutagen>=1.40', 'chardet>=3.0.4'],
    zip_safe=False,
    scripts=['bin/cue2report',
             'bin/cue2points',
             'bin/cdda2tracks'],
    author='AndreyVM',
    author_email='newbie@auriz.ru',
    description=DESC,
    license='GNU GPLv3',
    keywords='cue cdda flac image tracks vorbis opus mp3',
    url='https://gitlab.com/newbie_/cuetoolkit')
