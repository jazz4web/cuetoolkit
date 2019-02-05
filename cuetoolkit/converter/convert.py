"""
    cuetoolkit.converter.convert
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    CDDAConverter can split only CDDA images to tracks.
    NotCDDAConverter can split only images which are not CDDA.
"""


from ..common import CDDACue, NotCDDACue
from ..exc import FileError
from .abstract import Converter


class CDDAConverter(Converter):
    def __init__(self, media_type, schema, quiet, prefix='track'):
        Converter.__init__(self, media_type, schema, quiet, prefix)
        self.cue = CDDACue()

    def _validate_image(self):
        length, cdda = self._count_length(self.couple.media)
        last_index = self.convert_to_number(self.cue.sift_points('append')[-1])
        if length - last_index < 2:
            raise FileError('media file is too short for this cuesheet')
        if cdda != 'CDDA':
            raise FileError(
                'only CDDA images may be splitted without the -n option')


class NotCDDAConverter(Converter):
    def __init__(self, media_type, schema, quiet, prefix='track'):
        Converter.__init__(self, media_type, schema, quiet, prefix)
        self.cue = NotCDDACue()

    def _validate_image(self):
        length, cdda = self._count_length(self.couple.media)
        last_index = self.convert_to_seconds(self.cue.sift_points('append')[-1])
        if length - last_index < 2:
            raise FileError('media file is too short for this cuesheet')
        if cdda == 'CDDA':
            raise FileError(
                'CDDA images may not be splitted with the -n option')
