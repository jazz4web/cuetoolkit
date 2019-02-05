"""
    cuetoolkit.report
    ~~~~~~~~~~~~~~~~~

    Its class Reporter can be used to extract CDDA-image data
    from the cuesheet and media file of the image and print
    a report on the screen. It can be used only with CDDA-images
    or single cuesheets.
"""


from .abstract import Decoder, HashCounter, LengthConverter, LengthCounter
from .common import Couple
from .exc import FileError


class Reporter(Decoder, HashCounter, LengthCounter, LengthConverter):
    """
    This can extract CDDA-image data and print a report.
    """
    def __init__(self):
        self.couple = Couple()
        self.cue = None
        self.length = None
        self.cdda = None
        self.hash = None
        self.durations = None

    def _count_durations(self, length, points):
        if length:
            box = list()
            box.append(self.convert_to_number(points[0]))
            for step, item in enumerate(points):
                if step > 0:
                    box.append(
                        round(self.convert_to_number(item) -
                              self.convert_to_number(points[step - 1]), 3))
            box.append(round(length - self.convert_to_number(points[-1]), 3))
            return box
        return None

    def parse(self, source, media_hash=False):
        """
        Parse cuesheet data before printing.
        :param source: cuesheet file name
        :param media_hash: True or False
        :return: None
        """
        self.couple.couple(source)
        if self.couple.media:
            from .common import CDDACue
            self.cue = CDDACue()
            self.cue.extract(source)
            self._check_decoder(self.couple.media)
            self.length, self.cdda = self._count_length(self.couple.media)
            points = self.cue.sift_points('append')
            self.durations = self._count_durations(self.length, points)
            last_index = self.convert_to_number(points[-1])
            if self.length - last_index < 2:
                raise FileError('unsuitable media file for this cuesheet')
            if media_hash:
                self.hash = self.count_hash(self.couple.media)
        else:
            from .common import Cue
            self.cue = Cue()
            self.cue.extract(source)

    def _form_data(self):
        if self.durations:
            captions = ('genre:', 'year:', 'disc id:',
                        'commentary:', 'artist:', 'album:',
                        'type:', 'md5 hash:', 'cuesheet file:',
                        'media file:', 'total length:', 'tracks total:')
            values = (self.cue.genre, self.cue.year, self.cue.d_id,
                      self.cue.comm, self.cue.art_a, self.cue.album,
                      self.cdda, self.hash, self.couple.cue_base,
                      self.couple.media_base,
                      self.convert_to_string(self.length),
                      str(int(self.cue.track[-1])))
        else:
            captions = ('genre:', 'year:', 'disc_id:', 'commentary:',
                        'artist:', 'album:', 'tracks total:')
            values = (self.cue.genre, self.cue.year, self.cue.d_id,
                      self.cue.comm, self.cue.art_a, self.cue.album,
                      str(int(self.cue.track[-1])))
        return captions, values, max(map(len, captions)) + 2

    def pprint(self):
        """
        Print the report on the screen.
        :return: None
        """
        if self.cue is None:
            raise RuntimeError('source cuesheet is not parsed yet')
        captions, values, max_length = self._form_data()
        for (caption, value) in zip(captions, values):
            if value:
                print('{0}{1:>{2}}'.format(
                    caption,
                    value,
                    max_length - len(caption) + len(value)))
        mtl = max(map(len, self.cue.title)) + 2
        mal = max(map(len, self.cue.artist)) + 2
        for st, tr in enumerate(self.cue.track):
            a = mal - len(self.cue.artist[st]) + len(self.cue.title[st])
            if self.durations:
                d = self.convert_to_string(self.durations[st])
                t = mtl - len(self.cue.title[st]) + len(d)
                print('{0}  {1}{2:>{4}}{3:>{5}}'.format(
                    tr, self.cue.artist[st], self.cue.title[st], d, a, t))
            else:
                print('{0}  {1}{2:>{3}}'.format(
                    tr, self.cue.artist[st], self.cue.title[st], a))
