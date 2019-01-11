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
            box.append(self._convert_to_number(points[0]))
            for step, item in enumerate(points):
                if step > 0:
                    box.append(
                        round(self._convert_to_number(item) -
                              self._convert_to_number(points[step - 1]), 3))
            box.append(round(length - self._convert_to_number(points[-1]), 3))
            return box
        return None

    def parse(self, source, media_hash=False):
        self.couple.couple(source)
        if self.couple.media:
            from .common import CueCDDA
            self.cue = CueCDDA()
            self.cue.extract(source)
            self._check_decoder(self.couple.media)
            if media_hash:
                self.hash = self._count_hash(self.couple.media)
            self.length, self.cdda = self._count_length(self.couple.media)
            self.durations = self._count_durations(
                self.length, self.cue.sift_points('append'))
        else:
            from .common import Cue
            self.cue = Cue()
            self.cue.extract(source)

    def pprint(self):
        # here we are
        pass
