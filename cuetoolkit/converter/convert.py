import json

from ..abstract import Encoder, MediaSplitter, LengthCounter
from ..common import Couple, CueCDDA
from ..mutagen.tagger import Tagger
from ..exc import FileError
from ..system import options_file


class Converter(MediaSplitter, Encoder, LengthCounter):
    def __init__(self, media_type, schema, quiet, prefix='track'):
        self.cfg = None
        self.couple = Couple()
        self.prefix = prefix
        self.media_type = media_type
        self.schema = schema
        self.quiet = quiet
        self.template = None
        self.cue = CueCDDA()
        self.tagger = None
        self.cmd = None

    @staticmethod
    def read_cfg(conf_file):
        try:
            with open(conf_file, 'r', encoding='utf-8') as config:
                return json.load(config)
        except (OSError, ValueError):
            print('warning:unable to read predefined options')
            return None

    def _solve_options(self, enc_options):
        if enc_options and isinstance(enc_options, list):
            return ' '.join(enc_options)
        return ''

    def _gen_parts(self, media_type):
        a_out, b_out = ' - -o %f"', ' - %f"'
        flac, ogg, opus = '', '-q 4', '--raw-rate 44100'
        mp3 = '--noreplaygain --lowpass -1 -V 0'
        parts = {each: dict() for each in ('flac', 'ogg', 'opus', 'mp3')}
        parts['flac'].setdefault('cust', '"cust ext=flac flac ')
        parts['ogg'].setdefault('cust', '"cust ext=ogg oggenc ')
        parts['opus'].setdefault('cust', '"cust ext=opus opusenc ')
        parts['mp3'].setdefault('cust', '"cust ext=mp3 lame ')
        parts['flac'].setdefault('out', a_out)
        parts['ogg'].setdefault('out', a_out)
        parts['opus'].setdefault('out', b_out)
        parts['mp3'].setdefault('out', b_out)
        parts['flac'].setdefault(
            'enc',
            self.cfg.get('flac').get('enc') or flac if self.cfg else flac)
        parts['ogg'].setdefault(
            'enc',
            self.cfg.get('ogg').get('enc') or ogg if self.cfg else ogg)
        parts['opus'].setdefault(
            'enc',
            self.cfg.get('opus').get('enc') or opus if self.cfg else opus)
        parts['mp3'].setdefault(
            'enc',
            self.cfg.get('mp3').get('enc') or mp3 if self.cfg else mp3)
        return (parts.get(media_type).get('cust'),
                parts.get(media_type).get('enc'),
                parts.get(media_type).get('out'))

    def _gen_head(self, quiet):
        if quiet:
            return 'shnsplit -a {0} -q -o '.format(self.prefix)
        return 'shnsplit -a {0} -o '.format(self.prefix)

    def _gen_cmd(self, media_type, enc_options, quiet):
        e, opts, output = self._gen_parts(media_type)
        opts = enc_options or opts
        return '{0}{1}{2}{3}'.format(self._gen_head(quiet), e, opts, output)

    def _validate_image(self):
        length, cdda = self._count_length(self.couple.media)
        last_index = self.convert_to_number(self.cue.sift_points('append')[-1])
        if length - last_index < 2:
            raise FileError('media file is too short for this cuesheet')
        if cdda != 'CDDA':
            raise FileError('only CDDA images may be splitted')

    def check_data(self, source, enc_options):
        self.cfg = self.read_cfg(options_file)
        enc_options = self._solve_options(enc_options)
        self.couple.couple(source)
        if self.couple.cue is None:
            raise FileError('there is no cuesheet')
        if self.couple.media is None:
            raise FileError('there is no media file')
        self._check_decoder(self.couple.media)
        self._check_encoder(self.media_type)
        self.template = '{0}*.{1}'.format(self.prefix, self.media_type)
        self.cue.extract(self.couple.cue)
        self._validate_image()
        self.cmd = '{0} "{1}"'.format(
            self._gen_cmd(self.media_type, enc_options, self.quiet),
            self.couple.media)
        self.tagger = Tagger()
        self.tagger.prepare(self.media_type)
