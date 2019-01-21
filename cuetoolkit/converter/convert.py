from ..common import Couple, CDDACue, NotCDDACue
from ..mutagen.tagger import Tagger
from ..exc import FileError
from .abstract import Converter


class CDDAConverter(Converter):
    def __init__(self, media_type, schema, quiet, prefix='track'):
        Converter.__init__(self, media_type, schema, quiet, prefix)
        self.couple = Couple()
        self.tagger = Tagger()
        self.cue = CDDACue()

    def _validate_image(self):
        length, cdda = self._count_length(self.couple.media)
        last_index = self.convert_to_number(self.cue.sift_points('append')[-1])
        if length - last_index < 2:
            raise FileError('media file is too short for this cuesheet')
        if cdda != 'CDDA':
            raise FileError(
                'only CDDA images may be splitted without the -n option')

    def check_data(self, source, enc_options):
        Converter.check_data(self, source, enc_options)
        self._validate_image()


class NotCDDAConverter(CDDAConverter):
    def __init__(self, media_type, schema, quiet, prefix='track'):
        Converter.__init__(self, media_type, schema, quiet, prefix)
        self.couple = Couple()
        self.tagger = Tagger()
        self.cue = NotCDDACue()

    def _validate_image(self):
        length, cdda = self._count_length(self.couple.media)
        last_index = self.convert_to_seconds(self.cue.sift_points('append')[-1])
        if length - last_index < 2:
            raise FileError('media file is too short for this cuesheet')
        if cdda == 'CDDA':
            raise FileError(
                'CDDA images may not be splitted with the -n option')
