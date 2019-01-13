import json
import os

from .exc import show_error


conf_dir = os.path.join(os.getenv('HOME'), '.config/cuetoolkit')
options_file = os.path.join(conf_dir, 'options')
enc = {'enc': None}
options = {codec: enc.copy() for codec in ('flac', 'ogg', 'opus', 'mp3')}


def write_cfg(conf_file, cfg):
    try:
        with open(conf_file, 'w', encoding='utf-8') as config:
            print(
                json.dumps(cfg, ensure_ascii=False, sort_keys=True, indent=2),
                file=config)
    except OSError:
        show_error('unable to write {}'.format(conf_file))
