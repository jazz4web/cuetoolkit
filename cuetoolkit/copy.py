"""
    cuetoolkit.copy
    ~~~~~~~~~~~~~~~

    Copy cuesheet data from one file to another, the encoding
    of this copy will be UTF-8. Russian cyrillic data in copy can be
    transliterated with latin symbols.
"""


import os
import re

from .abstract import Reader, Writer
from .symbols import rus


class CopyCue(Reader, Writer):
    """
    This can copy cuesheet data from one file to another.
    """
    def __init__(self, name, lang):
        """
        there is only one language currently available - 'ru'
        :param name: cuesheet file name
        :param lang: 'ru'
        """
        choices = {'ru': rus,}
        self.source = name
        self.trans = choices.get(lang)
        self.content = None

    def prepare(self):
        """
        Prepare the cuesheet data for copying.
        :return: None
        """
        self.content = self._read_file(self.source)
        if self.trans:
            pats = (re.compile(r'^PERFORMER +(.+)'),
                    re.compile(r'^TITLE +(.+)'),
                    re.compile(r'^ +TITLE +(.+)'),
                    re.compile(r'^ +PERFORMER +(.+)'))
            trans = str.maketrans(self.trans)
            for each in pats:
                for i in range(len(self.content)):
                    if each.match(self.content[i]):
                        self.content[i] = self.content[i].translate(trans)

    def copy(self, output='same'):
        """
        Create a copy for given cuesheet file.
        :param output: copy name
        :return: None
        """
        if output == 'same':
            output = os.path.splitext(
                os.path.basename(self.source))[0] + '.cue~'
        if self.save(self.content, output) is None:
            raise OSError('cannot create the target file')
