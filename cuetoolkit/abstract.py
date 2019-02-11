"""
    cuetoolkit.abstract
    ~~~~~~~~~~~~~~~~~~~

    This module contains abstract classes.
    Any of its classes cannot be used to create instances,
    I need them to prevent repeating myself later in following code.
"""


import collections
import os
import re
import shlex

from subprocess import Popen, PIPE

from chardet import detect

from .exc import FileError, InvalidCueError, ReqAppError


class Checker:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def check_dep(dependency):
        """
        Check if 'dependency' exists in any of PATH catalogs and return True,
        if it does, or None in other case.

        :param dependency: string
        :return: True or None
        """
        for path in os.getenv('PATH').split(':'):
            dep_bin = os.path.join(path, dependency)
            if os.path.exists(dep_bin):
                return True
        return None


class Decoder(Checker):
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
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
                raise ReqAppError('{0} is not installed'. format(app))


class Encoder(Decoder):
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    def _check_encoder(self, media):
        apps = {'flac': 'flac',
                'ogg': 'oggenc',
                'opus': 'opusenc',
                'mp3': 'lame'}
        app = apps.get(media)
        if not self.check_dep(app):
            raise ReqAppError('{} is not installed'.format(app))


class MediaSplitter:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def split_media(command, points):
        """
        Split a media file with 'command' in subprocess using 'points' as
        break points where 'command' must be a viable shntool command.
        :param points: list containing strings in format 'mm:ss.ff'
                       or 'mm:ss.nnn'
        :param command: string containing a viable shntool command
        :return: None
        """
        points = '\n'.join(points).encode('utf-8')
        cmd = shlex.split(command)
        with Popen(cmd, stdin=PIPE) as p:
            p.communicate(input=points)
        if p.returncode:
            raise RuntimeError('looks like media file is not valid')


class HashCounter:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def count_hash(media):
        """
        Count the md5 hash for given media file with shntool in subprocess.
        :param media: a string (file name)
        :return: string containing md5 hash of given media file
        """
        cmd = shlex.split('shnhash "{0}"'.format(media))
        with Popen(cmd, stdout=PIPE) as p:
            result = p.communicate()
        if p.returncode:
            raise RuntimeError('looks like media file is not valid')
        return result[0].decode('utf-8').split()[0]


class LengthConverter:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def convert_to_string(length):
        """
        Convert the given amount of seconds (length) to a string in format
        "mm:ss.nn".
        :param length: float
        :return: string
        """
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
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def convert_to_number(time_line):
        """
        Convert a given time_line in format "mm:ss.ff" to a floating point
        number expressing the amount of seconds (length).
        :param time_line: string in format "mm:ss.ff"
        :return: float
        """
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
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def convert_to_seconds(time_line):
        """
        Convert a given time line in format "mm:ss.nnn" to a floating point
        number expressing the amount of seconds (length).
        :param time_line: string in format "mm:ss.nnn"
        :return: float
        """
        mm, ss, nnn = re.split(r'[:.]', time_line)
        return int(mm) * 60 + int(ss) + int(nnn) / 1000

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
        else:
            cdda = 'not CDDA'
            return self.convert_to_seconds(result[0]), cdda


class Reader(Checker):
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
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


class Writer:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def save(content, output):
        """
        Create a new file with 'output' as a name and save data from 'content'
        into this file, 'content' is a list containing strings.
        :param content: list containing strings
        :param output: string
        :return: True or None
        """
        try:
            with open(output, 'w', encoding='utf-8') as f:
                for line in content:
                    print(line, file=f)
                print('Done!')
                return True
        except OSError:
            return None


class ContentTool:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def get_value(content, pattern):
        """
        Check if 'content' contains a string matching 'pattern' and return
        a required fragment of this string.
        :param content: list containing strings
        :param pattern: compiled regular expression
        :return: string
        """
        for line in content:
            box = pattern.match(line)
            if box:
                return box.group(1).strip('"')

    @staticmethod
    def get_values(content, pattern):
        """
        Check if 'content' contains strings matching 'pattern' and return
        a list containing a required fragments of these strings.
        :param content: list containing strings
        :param pattern: compiled regular expression
        :return: list of strings
        """
        return [pattern.match(line).group(1).strip('"') for line in content
                if pattern.match(line)]


class Extractor(Reader):
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    def _get_content(self, name):
        content = self._read_file(name)
        if isinstance(content, str):
            raise FileError(content)
        return content


class MetaData(ContentTool):
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
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


class NotCDDAPointsData:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def convert_time_line(line):
        """
        Convert a given time line in format "mm:ss:ff" to format "mm:ss.nnn".
        :param line: string in format "mm:ss:ff"
        :return: string in format "mm:ss.nnn"
        """
        if line:
            parts = line.split(':')
            nnn = round(int(parts[2]) / 0.075)
            return '{0}:{1}.{2:<0{3}}'.format(int(parts[0]), parts[1], nnn, 3)


class PointsData:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
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

    @staticmethod
    def match_indices(item, line, pats, store):
        index0 = pats.index0.match(line)
        index1 = pats.index1.match(line)
        if index0:
            store[item][0] = index0.group(1)
        if index1:
            store[item][1] = index1.group(1)

    def _extract_indices(self, content):
        store, bounds, pats = dict(), list(), self._pattern_indices()
        for line in content:
            if pats.track.match(line):
                key = pats.track.match(line).group(1)
                store[key] = [None, None]
                bounds.append(content.index(line))
        for step, item in enumerate(sorted(store)):
            if step < len(store) - 1:
                for line in content[bounds[step]:bounds[step + 1]]:
                    self.match_indices(item, line, pats, store)
            else:
                for line in content[bounds[step]:]:
                    self.match_indices(item, line, pats, store)
        self._validate_indices(store)
        if store['01'][0] == '00:00:00':
            store['01'][0] = None
        if store['01'][1] == '00:00:00':
            store['01'][1] = None
        return store

    @staticmethod
    def convert_time_line(line):
        """
        Convert a given time line in format "mm:ss:ff" to format "mm:ss.ff".
        :param line: string in format "mm:ss:ff"
        :return: string in format "mm:ss.ff"
        """
        if line:
            parts = line.split(':')
            return '{0}:{1}.{2}'.format(int(parts[0]), parts[1], parts[2])

    def _arrange_indices(self, content):
        indices = self._extract_indices(content)
        return {key: (self.convert_time_line(indices[key][0]),
                      self.convert_time_line(indices[key][1]))
                for key in indices}


class Rename:
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    @staticmethod
    def rename_file(file_name, step, cue):
        """
        Rename a given file in compliance with 'cue' content.
        :param file_name: string
        :param step: integer
        :param cue: instance of CueCDDA or NotCDDACue
        :return: string or None
        """
        title = re.sub(r'[\\/|?<>*:]', '~', cue.title[step])
        artist = re.sub(r'[\\/|?<>*:]', '~', cue.artist[step])
        extension = os.path.splitext(file_name)[1].lower()
        new_name = '{0} - {1} - {2}{3}'.format(
            cue.track[step], artist, title, extension)
        try:
            os.rename(file_name, new_name)
        except OSError:
            return None
        return new_name
