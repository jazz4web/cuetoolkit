import importlib.util

from ..exc import show_error

if importlib.util.find_spec('mutagen') is None:
    show_error('python3 module mutagen is not installed')
