import os


from ..exc import show_error
from ..system import conf_dir, options, options_file, write_cfg

if not os.path.exists(conf_dir):
    try:
        os.mkdir(conf_dir, mode=0o755)
    except OSError:
        show_error('unable to create the directory for configuration files')

if not os.path.exists(options_file):
    write_cfg(options_file, options)
