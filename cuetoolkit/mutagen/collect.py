"""
    cuetoolkit.mutagen.collect
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Its tools can be used to collect metadata from tracks
    of a given format and create specific cuesheet.
"""


from mutagen import flac, id3, mp3, oggopus, oggvorbis, MutagenError

from .. import version
from ..abstract import Writer
from ..exc import FileError


class TagCollector(Writer):
    """
    This can read metadata from files of given media type and create with
    this data a cuesheet file.
    """
    def __init__(self, media_type, album_type, empty):
        """
        :param media_type: one of these: 'flac', 'ogg', 'opus' or 'mp3'
        :param album_type: 'single' or 'various'
        :param empty: True of False
        """
        self.media_type = media_type
        self.album_type = album_type
        self.empty = empty
        self.cue_sheet = None
        self.ready = False

    def _check_id3version(self, files):
        check = True
        for item in files:
            message = '"{}": no suitable tag'.format(item)
            try:
                song = id3.ID3(item)
            except (MutagenError, OSError):
                check = False
                print(message)
            else:
                if song.version[0] == 1:
                    check = False
                    print(message)
        return check

    def _choose(self):
        choices = {'flac': flac.FLAC,
                   'ogg': oggvorbis.OggVorbis,
                   'opus': oggopus.OggOpus,
                   'mp3': mp3.EasyMP3}
        return choices[self.media_type]

    @staticmethod
    def get_numbers(files):
        n = len(files)
        w = len(str(n))
        if w == 1:
            w = 2
        return (str(i).zfill(w) for i in range(1, n + 1))

    def _get_metadata(self, files):
        store = {}
        tracks = self.get_numbers(files)
        for step, item in enumerate(tracks):
            try:
                song = self._choose()(files[step])
                store[item] = song
            except OSError:
                store[item] = {}
        return store

    def _check_metadata(self, files, store):
        check = True
        if self.album_type == 'various':
            values = ('artist', 'title', 'genre', 'date')
        else:
            values = ('artist', 'title')
            for i in ('genre', 'album', 'date'):
                for key in sorted(store):
                    if i in store[key]:
                        break
                else:
                    print('warning:{0} is unknown'.format(i))
                    check = False
        for step, key in enumerate(sorted(store)):
            for i in values:
                if i not in store[key]:
                    print('warning:"{0}": {1} is empty'.format(files[step], i))
                    check = False
        return check

    @staticmethod
    def get_value(value, store):
        for key in sorted(store):
            if value in store[key]:
                return store[key].get(value)[0]
        return 'empty'

    @staticmethod
    def get_values(value, store):
        values = list()
        for track in sorted(store):
            if value in store[track]:
                values.append(store[track].get(value)[0])
            else:
                values.append('empty')
        return values

    def _derive_data(self, store):
        derived = dict()
        derived['artist'] = self.get_values('artist', store)
        derived['title'] = self.get_values('title', store)
        if self.album_type == 'various':
            derived['tgenre'] = self.get_values('genre', store)
            derived['tdate'] = self.get_values('date', store)
            derived['genre'] = ''
            derived['date'] = ''
            derived['album'] = 'Collection'
        else:
            derived['tgenre'] = list()
            derived['tdate'] = list()
            derived['genre'] = self.get_value('genre', store)
            derived['album'] = self.get_value('album', store)
            derived['date'] = self.get_value('date', store)
        return derived

    def _gen_cue_sheet(self, files, derived):
        tracks = self.get_numbers(files)
        data = list()
        data.append('REM GENRE "{0}"'.format(derived['genre']))
        data.append('REM DATE "{0}"'.format(derived['date']))
        data.append('REM COMMENT "{0}"'.format('cuetoolkit-' + version))
        if self.album_type == 'single':
            data.append('PERFORMER "{0}"'.format(derived['artist'][0]))
            data.append('TITLE "{0}"'.format(derived['album']))
        elif self.album_type == 'various':
            data.append('PERFORMER "Various Artists"')
            data.append('TITLE "Collection"')
        for step, item in enumerate(tracks):
            data.append('  TRACK {0} AUDIO'.format(item))
            data.append('    FILE "{0}"'.format(files[step]))
            data.append('    TITLE "{0}"'.format(derived['title'][step]))
            data.append('    PERFORMER "{0}"'.format(derived['artist'][step]))
            if self.album_type == 'various':
                data.append('    TGENRE "{0}"'.format(derived['tgenre'][step]))
                data.append('    TDATE {0}'.format(derived['tdate'][step]))
        return data

    def prepare(self, files):
        """
        Get metadata from media files and prepare to create cuesheet.
        :param files: list of file names
        :return: None
        """
        if self.media_type == 'mp3':
            if not self._check_id3version(files) and not self.empty:
                raise FileError(
                    'some of your files have no ID3v2 tag, use -e option')
        store = self._get_metadata(files)
        if self._check_metadata(files, store) or self.empty:
            self.cue_sheet = self._gen_cue_sheet(
                files, self._derive_data(store))
        self.ready = True

    def create_file(self, target):
        """
        Create a cuesheet file.
        :param target: target file name
        :return: None
        """
        if self.ready:
            if self.empty:
                if self.save(self.cue_sheet, target) is None:
                    raise OSError('cannot create the target file')
            else:
                if self.cue_sheet:
                    if self.save(self.cue_sheet, target) is None:
                        raise OSError('cannot create the target file')
                else:
                    raise FileError(
                        'your files contain empty fields, use -e option')
        else:
            raise RuntimeError(
                'data is not ready, use the prepare method first')
