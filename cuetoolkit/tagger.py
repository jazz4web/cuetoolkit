import glob

from .abstract import Rename
from .common import Cue, Couple
from .exc import AmountError
from .mutagen.tagger import Tagger


class TagWriter(Rename):
    def __init__(self):
        self.cue = Cue()
        self.tagger = Tagger()
        self.couple = Couple()
        self.files = None

    def prepare(self, media_type, source):
        self.cue.extract(source)
        self.tagger.prepare(media_type)
        self.couple.couple(source)
        self.files = [name for name in
                      sorted(glob.glob('*.{0}'.format(media_type)))
                      if name != self.couple.media_base]
        if len(self.cue.track) != len(self.files):
            raise AmountError(
                '{0} tracks in cuesheet and {1} files in CWD'
                .format(len(self.cue.track), len(self.files)))

    def write_metadata(self, rename, quiet):
        block = max(len(name) for name in self.files) + 2
        for step, item in enumerate(self.files):
            self.tagger.write_meta(item, step, self.cue)
            if rename:
                new_name = self.rename_file(item, step, self.cue)
                if not quiet:
                    print('{0:<{2}}->  {1}'
                          .format(item, new_name or 'skipped', block))
            if not quiet and not rename:
                print('{0:<{1}}done'.format(item, block))
