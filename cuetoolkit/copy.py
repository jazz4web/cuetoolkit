import os
import re

from .abstract import Reader, Writer
from .symbols import rus


class CopyCue(Reader, Writer):
    def __init__(self, name, lang):
        choices = {'ru': rus,}
        self.source = name
        self.trans = choices.get(lang)
        self.content = None

    def prepare(self):
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
        if output == 'same':
            output = os.path.splitext(
                os.path.basename(self.source))[0] + '.cue~'
        if self.save(self.content, output) is None:
            raise OSError('cannot create the target file')
