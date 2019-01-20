import glob
import os

from ..exc import show_error


class Cleaner:
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
