"""
    cuetoolkit.converter.abstract
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Converter is the abstract class, you don't want to create its instances.
    The target classes for use are located in cuetoolkit.converter.convert
    module.
"""


import glob
import json
import os
import time

from ..abstract import MediaSplitter, Encoder, LengthCounter, Rename
from ..common import Couple
from ..mutagen.tagger import Tagger
from ..exc import FileError, show_error
from ..system import options_file


class Converter(MediaSplitter, Encoder, LengthCounter, Rename):
    """
    This is an abstract class, you do not want to create instances of this
    class because they will be able to do almost nothing. Nevertheless,
    I need this class as a super class to create other classes in cuetoolkit.
    """
    def __init__(self, media_type, schema, quiet, prefix='track'):
        self.prefix = prefix
        self.media_type = media_type
        self.schema = schema
        self.quiet = quiet
        self.tagger = Tagger()
        self.couple = Couple()
        self.cfg = None
        self.template = None
        self.cue = None
        self.cmd = None

    def _solve_options(self, enc_options):
        if enc_options and isinstance(enc_options, list):
            return ' '.join(enc_options)
        return ''

    def _gen_parts(self, media_type):
        a_out, b_out = ' - -o %f"', ' - %f"'
        flac, ogg, mp3 = '', '-q 4', '--noreplaygain --lowpass -1 -V 0'
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
            self.cfg.get('opus').get('enc') or flac if self.cfg else flac)
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

    def _detect_gaps(self):
        junk = list()
        if self.schema == 'split':
            step = 1
            for key in sorted(self.cue.store):
                if key == '01':
                    if self.cue.store[key][1]:
                        junk.append('{0}{1}.{2}'.format(
                            self.prefix,
                            str(step).zfill(2),
                            self.media_type))
                        step += 1
                else:
                    if self.cue.store[key][0]:
                        step += 1
                        junk.append('{0}{1}.{2}'.format(
                            self.prefix,
                            str(step).zfill(2),
                            self.media_type))
                        step += 1
                    else:
                        step += 1
        return junk

    def clean(self, thread, rename):
        step = 0
        files = sorted(glob.glob(self.template))
        junk = self._detect_gaps()
        while thread.is_alive():
            time.sleep(0.1)
            if junk:
                self.remove_gaps(junk)
            if len(files) < len(sorted(glob.glob(self.template))):
                files = sorted(glob.glob(self.template))
                if len(files) >= 2:
                    self.tagger.write_meta(files[-2], step, self.cue)
                    if rename:
                        self.rename_file(files[-2], step, self.cue)
                    files = sorted(glob.glob(self.template))
                    step += 1
        if files:
            self.tagger.write_meta(files[-1], step, self.cue)
            if rename:
                self.rename_file(files[-1], step, self.cue)

    def _validate_image(self):
        pass

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
        self.tagger.prepare(self.media_type)

    @staticmethod
    def read_cfg(conf_file):
        try:
            with open(conf_file, 'r', encoding='utf-8') as config:
                return json.load(config)
        except (OSError, ValueError):
            print('warning:unable to read predefined options')
            return None

    @staticmethod
    def clean_cwd(template):
        junk = glob.glob(template)
        if junk:
            for item in junk:
                try:
                    os.remove(item)
                except OSError:
                    show_error('current working directory is not writable')

    @staticmethod
    def remove_gaps(junk):
        for gap in junk:
            if gap in os.listdir('.'):
                try:
                    os.remove(gap)
                except OSError:
                    show_error('cannot remove {0}'.format(gap))
