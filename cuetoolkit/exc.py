import os
import sys


def show_error(msg, code=1):
    print(
        os.path.basename(sys.argv[0]),
        'error',
        msg,
        sep=':',
        file=sys.stderr)
    sys.exit(code)


class ReqAppError(OSError):
    pass


class FileError(Exception):
    pass


class InvalidCueError(Exception):
    pass
