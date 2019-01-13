import collections
import os
import re
import shlex

from subprocess import Popen, PIPE

from chardet import detect

from .exc import FileError, InvalidCueError, ReqAppError


class Checker:
    @staticmethod
    def check_dep(dependency):
        for path in os.getenv('PATH').split(':'):
            dep_bin = os.path.join(path, dependency)
            if os.path.exists(dep_bin):
                return True
        return None


class Decoder(Checker):
    def _check_decoder(self, media):
        if media:
            if not self.check_dep('shntool'):
                raise ReqAppError('shntool is not installed')
            apps = {'.flac': 'flac',
                    '.ape': 'mac',
                    '.wv': 'wvunpack',
                    '.wav': None}
            app = apps.get(os.path.splitext(media)[1])
            if app and not self.check_dep(app):
                raise ReqAppError('{} is not installed'. format(app))


class Encoder(Decoder):
    def _check_encoder(self, media):
        apps = {'flac': 'flac',
                'ogg': 'oggenc',
                'opus': 'opusenc',
                'mp3': 'lame'}
        app = apps.get(media)
        if not self.check_dep(app):
            raise ReqAppError('{} is not installed'.format(app))


class MediaSplitter:
    @staticmethod
    def split_media(points, command):
        points = '\n'.join(points).encode('utf-8')
        cmd = shlex.split(command)
        with Popen(cmd, stdin=PIPE) as p:
            p.communicate(input=points)
        if p.returncode:
            raise RuntimeError('looks like media file is not valid')


class HashCounter:
    @staticmethod
    def count_hash(media):
        cmd = shlex.split('shnhash "{}"'.format(media))
        with Popen(cmd, stdout=PIPE) as p:
            result = p.communicate()
        if p.returncode:
            raise RuntimeError('looks like media file is not valid')
        return result[0].decode('utf-8').split()[0]


class LengthConverter:
    @staticmethod
    def convert_to_string(length):
        m, s = int(length) // 60, int(length) % 60
        n = int(round(length - int(length), 1) * 10)
        if n > 9:
            s += 1
            n = 0
            if s > 59:
                m += 1
                s = 0
        return '{:0{w}d}:{:0{w}d}.{}'.format(m, s, n, w=2)


class TLConverter:
    @staticmethod
    def convert_to_number(time_line):
        mm, ss, ff = re.split(r'[:.]', time_line)
        if int(ss) > 59 or int(ff) > 74:
            raise InvalidCueError('this cuesheet has an invalid timestamp')
        ss = int(mm) * 60 + int(ss)
        nnn = round(int(ff) / 0.075)
        if nnn > 999:
            ss += 1
            nnn = 0
        return ss + nnn / 1000


class LengthCounter(TLConverter):
    def _count_length(self, media):
        if media is None:
            return None, None
        cmd = shlex.split('shnlen -ct "{}"'.format(media))
        with Popen(cmd, stdout=PIPE, stderr=PIPE) as p:
            result = p.communicate()
        if p.returncode:
            raise RuntimeError('looks like media file is not valid')
        result = result[0].decode('utf-8').split()
        cdda = result[3]
        if cdda == '---':
            cdda = 'CDDA'
        return self.convert_to_number(result[0]), cdda


class Reader(Checker):
    def _detect_file_type(self, name):
        required = 'file'
        if self.check_dep(required) is None:
            raise ReqAppError('{} is not installed'.format(required))
        cmd = shlex.split('file -b -i "{}"'.format(name))
        with Popen(cmd, stdout=PIPE, stderr=PIPE) as p:
            result = p.communicate()
        if p.returncode:
            raise RuntimeError('something bad happened')
        return result[0].decode('utf-8')

    def _read_file(self, name):
        if self._detect_file_type(name).split('/')[0] != 'text':
            return 'this file is not a cuesheet'
        try:
            with open(name, 'rb') as f:
                enc = detect(f.read())['encoding']
                f.seek(0)
                return [line.decode(enc).rstrip() for line in f]
        except (OSError, ValueError):
            return 'this cuesheet has bad encoding or cannot be read'


class ContentTool:
    @staticmethod
    def get_value(content, pattern):
        for line in content:
            box = pattern.match(line)
            if box:
                return box.group(1).strip('"')

    @staticmethod
    def get_values(content, pattern):
        return [pattern.match(line).group(1).strip('"') for line in content
                if pattern.match(line)]


class Extractor(Reader):
    def _get_content(self, name):
        content = self._read_file(name)
        if isinstance(content, str):
            raise FileError(content)
        return content


class MetaData(ContentTool):
    def _pattern_data(self):
        pattern = collections.namedtuple(
            'Pattern',
            ['art_a',
             'album',
             'genre',
             'd_id',
             'year',
             'comm',
             'title',
             'artist',
             'tgenre',
             'tdate',
             'track'])
        return pattern(
            art_a=re.compile(r'^PERFORMER +(.+)'),
            album=re.compile(r'^TITLE +(.+)'),
            genre=re.compile(r'^REM GENRE +(.+)'),
            d_id=re.compile(r'^REM DISCID +(.+)'),
            year=re.compile(r'^REM DATE +(.+)'),
            comm=re.compile(r'^REM COMMENT +(.+)'),
            title=re.compile(r'^ +TITLE +(.+)'),
            artist=re.compile(r'^ +PERFORMER +(.+)'),
            tgenre=re.compile(r'^ +TGENRE +(.+)'),
            tdate=re.compile(r'^ +TDATE +(.+)'),
            track=re.compile(r'^ +TRACK +(\d+) +(.+)'))


class PointsData:
    def _pattern_indices(self):
        pattern = collections.namedtuple(
            'Pattern',
            ['track', 'index0', 'index1'])
        return pattern(
            track=re.compile(r'^ +TRACK +(\d+) +(.+)'),
            index0=re.compile(r'^ +INDEX 00 +(\d{2}:\d{2}:\d{2})'),
            index1=re.compile(r'^ +INDEX 01 +(\d{2}:\d{2}:\d{2})'))

    def _validate_indices(self, store):
        if not store:
            raise InvalidCueError('no indices in your cuesheet')
        for key in sorted(store):
            if key != '01' and not store[key][1]:
                raise InvalidCueError('bad indices for track {}'.format(key))

    def _extract_indices(self, content):
        store = dict()
        pats = self._pattern_indices()
        for line in content:
            if pats.track.match(line):
                key = pats.track.match(line).group(1)
                store[key] = [None, None]
            elif pats.index0.match(line):
                store[key][0] = pats.index0.match(line).group(1)
            elif pats.index1.match(line):
                store[key][1] = pats.index1.match(line).group(1)
        self._validate_indices(store)
        if store['01'][0] == '00:00:00':
            store['01'][0] = None
        if store['01'][1] == '00:00:00':
            store['01'][1] = None
        return store

    @staticmethod
    def convert_time_line(line):
        if line:
            parts = line.split(':')
            return '{0}:{1}.{2}'.format(int(parts[0]), parts[1], parts[2])

    def _arrange_indices(self, content):
        indices = self._extract_indices(content)
        return {key: (self.convert_time_line(indices[key][0]),
                      self.convert_time_line(indices[key][1]))
                for key in indices}
