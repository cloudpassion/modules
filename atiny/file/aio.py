import os
import hashlib
import zipfile
import lzma
try:
    import magic
except ImportError:
    pass

import re
import imghdr
import io
import gzip as gzip_module

import ujson as json

from datetime import datetime
from pathlib import Path

try:
    from log import logger
except ImportError:
    from ..log import logger


def make_zipfile(output_filename, source_dir):
    relroot = os.path.abspath(os.path.join(source_dir, os.pardir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_LZMA) as zip:
        for root, dirs, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zip.write(root, os.path.relpath(root, relroot))
            for file in files:
                filename = os.path.join(root, file)
                if os.path.isfile(filename): # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), file)
                    zip.write(filename, arcname)


def zip_unpack(file_path, output_dir):
    zip_ref = zipfile.ZipFile(file_path, 'r')
    zip_ref.extractall(output_dir)
    zip_ref.close()


# files dirs
def create_date_dir(main_dir, year=True, mon=True, day=False):

    now = datetime.now()

    return f'{main_dir}' \
           f'{now.strftime("/%Y") if year else ""}' \
           f'{now.strftime("/%m") if mon else ""}' \
           f'{now.strftime("/%d") if day else ""}'


def create_dirname(fname):
    os.makedirs(os.path.dirname(fname), exist_ok=True)


def create_dir(dname, parents=True):
    path = Path(dname)
    path.mkdir(parents=parents, exist_ok=True)


# CREATE SYMLINK
def create_symlink(src, dst, _force=False):
    if not os.path.exists(dst) or _force:
        if os.path.isfile(dst) or os.path.islink(dst):
            os.remove(dst)
        os.symlink(src, dst)


class FOpenMode:

    def __init__(self, file_path, mode):
        self.path = file_path
        self.m = None
        self.f = None
        if mode == 'fwa':
            self.fwa()
        elif mode == 'frw':
            self.frw()
        elif mode == 'frwp':
            self.frwp()

    def fwa(self):
        if os.path.isfile(self.path):
            self.m = 'a'
        else:
            self.m = 'w'
        return self.m

    def frw(self):
        if os.path.isfile(self.path):
            self.m = 'r'
        else:
            self.m = 'w'
        return self.m

    def frwp(self):
        if os.path.isfile(self.path):
            self.m = 'r+'
        else:
            self.m = 'w+'
        return self.m

    def open(self):
        self.f = open(self.path, self.m)

    def close(self):
        if self.f:
            self.f.close()


class FileUtils(FOpenMode):

    file_exists: bool
    path_exists: bool

    def __init__(self, file_path):
        self.path = file_path
        self.md5 = ''

        self.file_exists = False
        self.path_exists = False

        try:
            if os.path.isfile(file_path):
                self.file_exists = True
        except Exception:
            pass

        if not self.path_exists:
            try:
                if os.path.islink(file_path):
                    self.path_exists = True
            except Exception:
                pass

    def file_size(self, in_bytes=False):
        try:
            if not in_bytes:
                return self.convert_bytes(os.stat(self.path).st_size)
            else:
                return os.stat(self.path).st_size
        except:
            self.path.seek(0)
            return len(self.path.read())

    def convert_bytes(self, num):
        """
        this function will convert bytes to MB.... GB... etc
        """
        for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
            if num < 1024.0:
                return "%3.1f_%s" % (num, x)
            num /= 1024.0

    def md5sum(self):
        try:
            hash_md5 = hashlib.md5()
            with open(self.path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            self.md5 = hash_md5.hexdigest()
            return self.md5
        except:
            return self.md5_checksum(self.path)

    def md5_checksum(self, data: (str, bytearray, bytes, io.BufferedReader, io.FileIO)) -> str:
        """
        create md5 checksum
        :param data: input data to check md5 checksum
        :type data: str, bytearray, bytes, io.BufferedReader, io.FileIO
        :return: md5 hash
        :rtype: str
        """

        # byte
        if isinstance(data, (bytes, bytearray)):
            md5 = hashlib.md5(data).hexdigest()

        # file
        elif isinstance(data, str) and os.access(data, os.R_OK):
            md5 = hashlib.md5(open(data, 'rb').read()).hexdigest()

        # file object
        elif isinstance(data, (io.BufferedReader, io.FileIO)):
            md5 = hashlib.md5(data.read()).hexdigest()

        # string
        elif isinstance(data, str):
            md5 = hashlib.md5(data.encode()).hexdigest()

        elif isinstance(data, io.BytesIO):
            data.seek(0)
            md5 = hashlib.md5(data.read()).hexdigest()
        else:
            raise ValueError('invalid input. input must be string, byte or file')

        self.md5 = md5
        return md5

    def md5sum_old(self):
        self.md5 = hashlib.md5(open(self.path, 'rb').read()).hexdigest()
        return self.md5

    def tail(self, f, n, offset=None):
        """Reads a n lines from f with an offset of offset lines.  The return
        value is a tuple in the form ``(lines, has_more)`` where `has_more` is
        an indicator that is `True` if there are more lines in the file.
        """
        avg_line_length = 74
        to_read = n + (offset or 0)

        while 1:
            try:
                f.seek(-(avg_line_length * to_read), 2)
            except IOError:
                # woops.  apparently file is smaller than what we want
                # to step back, go to the beginning instead
                f.seek(0)
            pos = f.tell()
            lines = f.read().splitlines()
            if len(lines) >= to_read or pos == 0:
                return lines[-to_read:offset]
            avg_line_length *= 1.3

    def linux_tail(self, _n, offset=None):
        with open(self.path, 'r') as fr:
            return (self.tail(fr, _n, offset=offset))

    def tac_echo(self, line):
        with open(self.path, self.frwp()) as _f:
            content = _f.read()
            _f.seek(0, 0)
            _f.write(line.rstrip('\r\n') + '\n' + content)

    def json_from_file(self, gzip=True):

        if self.path_exists:
            if gzip:
                read_func = gzip_module.open
            else:
                read_func = open

            with read_func(self.path, 'r') as rf:
                try:
                    js = json.loads(rf.read())
                except Exception:
                    js = {}
        else:
            js = {}

        return js if js else {}

    def json_to_file(self, write_js, update=False, gzip=True):

        if gzip:
            file_func = gzip_module.open
        else:
            file_func = open

        if self.path_exists:
            if update:
                with file_func(self.path, 'r') as rf:
                    try:
                        old_js = json.loads(rf.read())
                    except Exception:
                        old_js = {}
                if old_js:
                    old_js.update(write_js if write_js else {})
                    write_js = old_js
        else:
            Path(
                os.path.dirname(
                    os.path.abspath(
                        self.path
                    ))
            ).mkdir(parents=True, exist_ok=True)

        with file_func(self.path, 'w') as wf:
            wf.write(json.dumps(dict(write_js) if dict(write_js) else {}))

        return write_js if write_js else {}


class FileMagic:

    photo_set = {'png', 'bmp', 'jpeg', 'jpg'}
    video_set = {'mp4', 'avi', 'mpeg'}
    animation_set = {'gif', 'webp'}
    audio_set = {'mp3', 'ogg', 'flac'}

    sets = {
        'image': photo_set, 'video': video_set,
        'audio': audio_set, 'animation': animation_set
    }

    def __init__(self, file_path, _type=None):
        self.path = file_path
        self.type = _type
        self.file_ext = ''

        if _type:
            if _type == 'image':
                self.check_in = self.photo_set
            elif _type == 'video':
                self.check_in = self.video_set
            elif _type == 'audio':
                self.check_in = self.audio_set
            elif _type == 'animation':
                self.check_in = self.animation_set
            else:
                logger.debug(f'new search type: {_type}')
                self.check_in = 'new'
        else:
            self.check_in = False

    def get_mime(self, _what_str):

        for set_key, set_value in self.sets.items():
            for _type in set_value:
                if _type in _what_str:
                    return set_key
        else:
            logger.debug('new type: '+_what_str)
            return 'document'

    def safe_ext(self, _magic):
        #logger.info(f'check_ext: {_magic}')
        try:
            if re.search('/', _magic):
                self.file_ext = _magic.split('/')[1]
            else:
                self.file_ext = _magic
        except:
            log_stack.error(f'safe_ext.check: {_magic}')

    def file_type(self, _what_str):

        logger.debug(_what_str)
        self.safe_ext(_what_str)

        if not self.check_in:
            return self.get_mime(_what_str)
        elif self.check_in == 'new':
            logger.info(f'new type {self.check_in=}')
        else:
            return self.get_mime(_what_str)

    def check(self):
        if not os.path.isfile(self.path):
            logger.error(f'File: {self.path} don\'t exists {os.getcwd()=}')
            return

        _check_what = imghdr.what(self.path)
        logger.info(f'FileMagic:_check_img: {str(_check_what)}')

        if _check_what:
            return self.file_type(_check_what)
        else:
            try:
                _magic_file = str(magic.from_file(self.path, mime=True))
                return self.file_type(_magic_file)
            except BaseException:
                log_stack.error(f'magic.from_file: {self.path}')

