import os

from . import version
from .abstract import Extractor, MetaData, PointsData
from .exc import FileError, InvalidCueError


class Cue(MetaData, Extractor):
    def __init__(self):
        self.art_a = None
        self.album = None
        self.genre = None
        self.d_id = None
        self.year = None
        self.comm = None
        self.comment = None
        self.title = None
        self.artist = None
        self.tgenre = None
        self.tdate = None
        self.track = None

    def _validate_metadata(self):
        for i in sorted(self.__dict__):
            if i in ('album', 'art_a', 'track', 'title'):
                if not self.__dict__[i]:
                    raise InvalidCueError('this cuesheet is not valid')
        if len(self.track) != len(self.title):
            raise InvalidCueError('this cuesheet is not valid')

    def extract(self, source, noreturn=True):
        content = self._get_content(source)
        pats = self._pattern_data()
        self.art_a = self.get_value(content, pats.art_a)
        self.album = self.get_value(content, pats.album)
        self.genre = self.get_value(content, pats.genre)
        self.d_id = self.get_value(content, pats.d_id)
        self.year = self.get_value(content, pats.year)
        self.comm = self.get_value(content, pats.comm)
        self.comment = (self.comm or 'cuetoolkit-' + version) + '/' +\
                       (self.d_id or 'unknown disc')
        self.title = self.get_values(content, pats.title)
        self.artist = self.get_values(content, pats.artist)
        self.track = self.get_values(content, pats.track)
        if not self.artist and self.art_a:
            self.artist = [self.art_a] * len(self.track)
        self.tgenre = self.get_values(content, pats.tgenre) or None
        self.tdate = self.get_values(content, pats.tdate) or None
        self._validate_metadata()
        if not noreturn:
            return content
        return None


class CuePoints(PointsData, Extractor):
    def __init__(self):
        self.store = None

    def extract(self, source):
        content = self._get_content(source)
        self.store = self._arrange_indices(content)

    def sift_points(self, schema):
        if self.store is None:
            raise RuntimeError('source is not extracted yet')
        if schema not in ('append', 'prepend', 'split'):
            raise ValueError('{} is not a valid schema'.format(schema))
        points = list()
        for key in sorted(self.store):
            if schema == 'append' and key != '01':
                points.append(self.store[key][1])
            elif schema == 'prepend':
                if self.store[key][0] and key != '01':
                    points.append(self.store[key][0])
                elif not self.store[key][0] and key != '01':
                    points.append(self.store[key][1])
            elif schema == 'split':
                if self.store[key][0]:
                    points.append(self.store[key][0])
                if self.store[key][1]:
                    points.append(self.store[key][1])
        return points


class CueCDDA(Cue, CuePoints):
    def __init__(self):
        Cue.__init__(self)
        self.store = None

    def extract(self, source, noreturn=False):
        if noreturn:
            raise ValueError('noreturn cannot be True')
        content = Cue.extract(self, source, noreturn=noreturn)
        self.store = self._arrange_indices(content)


class Couple:
    def __init__(self):
        self.cue = None
        self.media = None

    @property
    def media_base(self):
        if self.media:
            return os.path.basename(self.media)
        return None

    @media_base.setter
    def media_base(self, value):
        raise AttributeError('media_base cannot be set')

    @property
    def cue_base(self):
        if self.cue:
            return os.path.basename(self.cue)
        return None

    @cue_base.setter
    def cue_base(self, value):
        raise AttributeError('cue_base cannot be set')

    @staticmethod
    def find_cue(home, name, source):
        cue = [os.path.join(home, item) for item in os.listdir(home)
               if os.path.splitext(item) == (name, '.cue')]
        if not cue:
            # the first is cue, the second is media
            return None, os.path.realpath(source)
        # the first is cue, the second is media
        return os.path.realpath(cue[0]), os.path.realpath(source)

    @staticmethod
    def find_media(home, name, source, medias):
        media = [os.path.join(home, item) for item in os.listdir(home)
                 if os.path.splitext(item)[1].lower() in medias and
                 os.path.splitext(item)[0] == name]
        if not media:
            # the first is cue, the second is media
            return os.path.realpath(source), None
        # the first is cue, the second is media
        return os.path.realpath(source), os.path.realpath(media[0])

    def _define_couple(self, ext, name, source, home, medias):
        if ext not in medias and ext != '.cue':
            raise FileError('unsuitable file for this app')
        if ext in medias:
            return self.find_cue(home, name, source)
        elif ext == '.cue':
            return self.find_media(home, name, source, medias)

    def couple(self, source):
        if not os.path.exists(source):
            raise FileNotFoundError('"{}" does not exist'.format(source))
        name, ext = os.path.splitext(os.path.basename(source))
        # the first is cue, the second is media
        self.cue, self.media = self._define_couple(
            ext,
            name,
            source,
            os.path.dirname(source) or '.',
            ('.ape', '.flac', '.wav', '.wv'))
