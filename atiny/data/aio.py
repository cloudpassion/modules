import logging
import sys

try:
    import configparser
except ImportError:
    pass

import random
import string
try:
    import psutil
except ImportError:
    pass
import json
import os

from collections import defaultdict
from bs4 import BeautifulSoup

from .log import logger


class JSONObject:
    def __init__(self, _dict):
        vars(self).update(_dict)


def json_as_class(resp_text, encoding='utf8'):
    #logger.info(f'type: {type(resp_text)}, resp: {resp_text}')
    if isinstance(resp_text, dict):
        return json.loads(json.dumps(resp_text), object_hook=JSONObject)
    elif not resp_text:
        return json.loads('{}', object_hook=JSONObject)
    else:
        return json.loads(resp_text.decode(encoding), object_hook=JSONObject)


class MyTextClass:

    def tg_prepare_text(self, text):

        soup = BeautifulSoup(text, 'lxml')
        _text = ''.join(soup.findAll(text=True))

        return _text


class MyConfig(configparser.ConfigParser):
    path = None

    def init(self, config_path):
        self.path = config_path
        if not os.path.isfile(config_path):
            raise FileNotFoundError(config_path)
        self.read(config_path)
        return self

    def get_val(self, section, var, _type=str, default=''):
        try:
            if _type is bool:
                return self.getboolean(section, var)
            elif _type is int:
                return self.getint(section, var)
            elif _type is float:
                return self.getfloat(section, var)
            else:
                return self.get(section, var)

        except:
            if default == 'raise':
                #logger_stack.debug(f'MyConfig.get_val: return default: {default}')
                raise Exception
            return default


class MyArgsClass:

    def __init__(self):
        self.args = self.args_to_dict()
        self.line = self.get_line()

    def get_line(self):
        tmp = []
        for k, v in self.args.items():
            if isinstance(k, int):
                tmp.append('"'+str(v)+'"')
            else:
                tmp.append('"--'+k+'='+str(v)+'"')

        return ' '.join(tmp)

    def args_to_dict(self):
        tmp = defaultdict(bool, {})
        n = 0

        for _arg in sys.argv:
            if _arg.startswith('--'):
                (arg, val) = _arg.split("=")
                arg = arg[2:]

                if arg in tmp:
                    tmp[arg].append(val)
                else:
                    tmp[arg] = val
            else:
                tmp[n] = _arg
                n += 1

        return tmp

    def set_args(self, args_dict):
        self.args = defaultdict(bool, args_dict)
        self.line = self.get_line()


class MyProcessClass:

    def __init__(self, pid=None, name=None):

        if not pid and not name:
            self.name = None
            self.pid = None
            self.exists = None
            self.proc_name = None
            return

        self.process = psutil.Process(pid)

        self.name = name
        self.pid = int(pid)

        self.exists = psutil.pid_exists(self.pid)
        self.proc_name = self.process.name()

    def check_exists(self):
        if self.exists:
            if self.name == self.proc_name:
                self.exists = True
            else:
                self.exists = False


class NoAttr(object):
    def __getattr__(self, item):
        return None


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def data_size(self, _data):
    """ this function will return the data size
    """
    return convert_bytes(len(_data))


def convert_bytes(num):
    """
    this function will convert bytes to MB.... GB... etc
    """
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if num < 1024.0:
            return "%3.1f_%s" % (num, x)
        num /= 1024.0


def random_string(string_length=10, letters=string.ascii_letters + string.digits):
    """Generate a random string of fixed length """
    return ''.join(random.choice(letters) for i in range(string_length))


def randomString(string_length=10, letters=string.ascii_letters + string.digits):
    return random_string(string_length, letters)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


#def cava_progress(percent, path='/home/' + os.getenv('USER') + '/.i3/coub.log'):
#    ret = r''
#    for i in range(0, 9):
#        if percent > (i * 10):
#            ret += '1 '
#        else:
#            ret += '0 '
#
#    with open(path) as cw:
#        cw.write(ret)


def defrd(x, y=0, _int=False):
    # http://disq.us/p/1y6jpai
    ''' A classical mathematical rounding by Voznica '''
    m = int('1'+'0'*y) # multiplier - how many positions to the right
    q = x*m # shift to the right by multiplier
    c = int(q) # new number
    i = int( (q-c)*10 ) # indicator number on the right
    if i >= 5:
        c += 1
    if _int:
        return int(c/m)
    else:
        return c/m


def get_list(js):
    js_list = []
    if not js:
        return js_list

    try:
        if isinstance(js, str):
            return (js, )
        r = js[0]
        for jj in js:
            js_list.append(jj)
    except IndexError:
        js_list.append(js)
    except KeyError:
        js_list.append(js)
    except TypeError:
        js_list.append(js)

    return js_list


# temp

def gen_dict_extract(key, var):
    if hasattr(var, 'items'):
        for k, v in var.items():
            if k == key:
                yield var

        for k, v in var.items():
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result

# {'settings': {'main_dict': {'api_coub': 123123}}, 'date': 123123, 'hdate': 123123}
# {'date': 123123, 'settings': {'main_dict': {}}}
# {'settings': {'main_dict': {}}}
# main_dict, api_coub
# main_dict, vk_api
# {'main_dict': {'api_coub': 123123}}
#
def gen_dict_extract_up(key, var, pre_key):
    found = False
    if hasattr(var, 'items'):
        for k, v in var.items():
            yield pre_key, var

        if not found:
            for k, v in var.items():
                if isinstance(v, dict):
                    for result in gen_dict_extract_up(key, v, k):
                        yield result
                elif isinstance(v, list):
                    for d in v:
                        for result in gen_dict_extract_up(key, d, k):
                            yield result

def gen_dict_extract_upzz(key, var, pre_key):
    logger.info(f'k: {key}, var: {var}, pre_key: {pre_key}')
    if not hasattr(var.get(pre_key), 'items'):
        for k, v in var[pre_key].items():
            if k == key:
                yield pre_key, {key: v}

        for k, v in var[pre_key].items():
            if isinstance(v, dict):
                for result in gen_dict_extract_up(key, {k: v}, pre_key):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract_up(key, {k: d}, pre_key):
                        yield result

def gen_val_extract(val, var):
    if hasattr(var, 'items'):
        for k, v in var.items():
            if v == val:
                yield var

        for k, v in var.items():
            if isinstance(v, dict):
                for result in gen_val_extract(val, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_val_extract(val, d):
                        yield result


def gen_key_extract(val, var):
    if hasattr(var, 'items'):
        for k, v in var.items():
            if v == val:
                yield var

        for k, v in var.items():
            if isinstance(v, dict):
                for result in gen_val_extract(val, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_val_extract(val, d):
                        yield result


def gen_dict_extract_keys(keys, var):
    if hasattr(var, 'items'):
        for key in keys:
            for k, v in var.items():
                if k == key:
                    yield {key: var}

            for k, v in var.items():
                if isinstance(v, dict):
                    for result in gen_dict_extract(key, v):
                        yield result
                elif isinstance(v, list):
                    for d in v:
                        for result in gen_dict_extract(key, d):
                            yield result


def find_pre_key(key, data, val):
    if hasattr(data, 'items'):
        for k, v in data.items():
            #logger.info(f'id_key: {id(key)}\n'
            #            f'id_k: {id(k)}\n'
            #            f'id_v: {id(v)}\n'
            #            f'id_val: {id(val)}')
            if isinstance(v, dict):
                if v is val:
                    yield k, v
            else:
                if k == key:
                    if v is val:
                        yield k, v

            if isinstance(v, dict):
                for result in find_pre_key(key, v, val):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in find_pre_key(key, d, val):
                        yield result


def find_pre_keyz(key, data, pre_data):
    if hasattr(data, 'items'):
        for k, v in data.items():
            if k == key:
                for pk, pv in pre_data.items():
                    #logger.info(f'pk: {pk}\n'
                    #            f'pv: {pv}\n'
                    #            f'da: {data}\n'
                    #            f'{pv is data}')
                    if pv is data:
                        yield pk, pv
            elif isinstance(v, dict):
                #logger.info(f'dict: key: {key}, v: {v}, data: {data}')
                for result in find_pre_key(key, v, data):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in find_pre_key(key, d, data):
                        yield result


def find_pre_val(val, data, pre_data):
    if hasattr(data, 'items'):
        for k, v in data.items():
            if v == val:
                for pk, pv in pre_data.items():
                    if pv is data:
                        yield pk, pv
            elif isinstance(v, dict):
                for result in find_pre_val(val, v, data):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in find_pre_val(val, d, data):
                        yield result


def get_table_val(vals, data):

    logger.info(f'keys: {vals}')
    _vals = list(reversed(vals))
    p = data.copy()
    ex_val = None
    while True:
        try:
            val = _vals.pop()
        except IndexError:
            break

        op = find_pre_val(val, p, p)
        #gen_val_extract(val, p)
        try:
            o = next(op)
            p = o[1]
            ex_val = o[0]
        except StopIteration:
            logger.info(f'p: {p}\n')
            break

    logger.info(f'p: {p}\n')
    logger.info(f'exv: {ex_val}')

    return ex_val, p


def get_table_data_up(key, d, val):
    #logger.info(f'd: {d}\nkeys: {key}, val: {val}\n')
    p = d.copy()
    ex_key = None

    #logger.info(f'exk: {ex_key}, p0: {p}')
    op = find_pre_key(key, p, val)
    try:
        o = next(op)
        ex_key = o[0]
    except StopIteration:
        pass

    #logger.info(f'o: {o}\n'
    #            f'exk: {ex_key}\n')

    return ex_key


def get_table_data_upd(keys, data):

    logger.info(f'keys: {keys}')
    o = None
    ex_key = 'settings'
    _keys = list(reversed(keys))
    p = data.copy()
    ok_exit = None
    while True:
        try:
            key = _keys.pop()
        except IndexError:
            ok_exit = True
            break

        op = find_pre_key(key, p, p)
        try:
            o = next(op)
            p = o[1]
            ex_key = o[0]
        except StopIteration:
            logger.info(f'o: {o}\n'
                        f'p: {p}\n'
                        f'exk: {ex_key}')
            break

    logger.info(f'o: {o}\n'
                f'p: {p}\n'
                f'exk: {ex_key}\n'
                f'oke: {ok_exit}')

    return {ex_key if ok_exit else ok_exit: o}


def get_table_data(keys, data):

    c_data = data.copy()
    _ret_safe = c_data
    for key in keys:
        c_data = gen_dict_extract(key, c_data)
        try:
            n = next(c_data)
            _ret_safe = n
            c_data = n[key]
        except StopIteration:
            logger.info(f'stop iter, key: {key}, keys: {keys}')
            break

    return _ret_safe


def gen_dict_extract_gitz(key, var):
    if hasattr(var, 'iteritems'):
        for k, v in var.iteritems():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result


class TransformData:

    # str ->
    # from hex string like r'60cb5b82ce912b556c6c6511' to b''
    def hexstr_to_bytes(self, hexstr: str):
        return bytes.fromhex(hexstr)

    # from r'' to b''
    def str_to_bytes(self, _str: str):
        return _str.encode()

    # bytes ->
    # from 'r' to b''
    def bytes_to_hex(self, _bt: bytes):
        return _bt.hex()

    # from bytes b'' to str r''
    def bytes_to_str(self, _bt: bytes):
        return str(_bt)

    def split_hexspace(self, hexstr):
        return ''.join(hexstr.split(' ')).lower()

    def str_xor(self, message: str, key: str):
        encrypted_string = ''
        for i in range(0, len(message)):
            word = message[i]
            ch = list(key)[i%len(key)]

            word_int = ord(word)
            ch_int = ord(ch)
            encrypted_string += chr(word_int^ch_int)
        return encrypted_string

    def str_unxor(self, message: str, key: str):

        unencrypted_string = ''
        for i in range(0, len(message)):
            word_char = message[i]
            ch_char = list(key)[i%len(key)]

            word_int = ord(word_char)
            ch_int = ord(ch_char)

            unencrypted_string += chr(word_int^ch_int)
        return unencrypted_string

    def bytes_xor(self, bt, key):
        return self.str_xor(self.bytes_to_str(bt), key)

    def bytes_unxor(self, bt, key):
        return self.str_unxor(self.bytes_to_str(bt), key)
# etalon
class LinkData:
    def __init__(self, pre_link=None, link=None, var=None):
        self.pre_link = pre_link
        self.link = link
        self.var = var


# table link by key
def link_dict_key(key, var, link, pre_link):
    if isinstance(var, dict):
        for k, v in var.items():
            if k == key:
                yield link, var, v
            else:
                yield from link_dict_key(key, v, var, link)
    elif isinstance(var, (list, tuple, set)):
        for d in var:
            yield from link_dict_key(key, d, var, link)


def get_table_link_bykey(key, data, pre_link=None):

    return_data = []

    op = link_dict_key(key, data, data, pre_link)
    while True:
        try:
            pre_link, link, value = next(op)
            return_data.append(LinkData(pre_link, link, value))
        except StopIteration:
            break

    return return_data


# get table link by val
def link_dict_val(val, var, link, pre_link=None):
    if isinstance(var, dict):
        for k, v in var.items():
            if v == val:
                yield link, var, k
            else:
                yield from link_dict_val(val, v, var, link)
    elif isinstance(var, (list, tuple, set)):
        for d in var:
            yield from link_dict_val(val, d, var, link)
    else:
        if val == var:
            yield pre_link, link, val


def get_table_link_byval(value, data, pre_link=None):

    return_data = []

    op = link_dict_val(value, data, data, pre_link)
    while True:
        try:
            pre_link, link, key = next(op)
            return_data.append(LinkData(pre_link, link, key))
        except StopIteration:
            break

    return return_data


# get table link by key, value
def link_dict_keyval(key, value, var, link, pre_link=None):
    if isinstance(var, dict):
        for k, v in var.items():
            if k == key and value == v:
                yield pre_link, link, var
            else:
                yield from link_dict_keyval(key, value, v, var, link)
    elif isinstance(var, (list, tuple, set)):
        for d in var:
            yield from link_dict_keyval(key, value, d, var, link)


def get_table_link_bykeyval(key, value, data, pre_link=None):

    return_data = []

    op = link_dict_keyval(key, value, data, data, pre_link)
    while True:
        try:
            pre_link, link, var = next(op)
            return_data.append(LinkData(pre_link, link, var))
        except StopIteration:
            break

    return return_data


def temp_mdata(key, val, d):

    #link, value = get_table_link_bykey(key, d)
    #all = get_table_link_bykey(key, d)
    all = get_table_link_byval(val, d)
    #op = find_pre_key(key, d, d)
    #op = find_pre_val(val, d, d)
    #op = find_pre_keyz(key, p, p)

    logger.info(f'all: {all}')


class ObjDataSearch:

    # get table link by key, value
    @staticmethod
    def link_dict_key_val(key, value, var, link, pre_link=None):
        if isinstance(var, dict):
            for k, v in var.items():
                if k == key and value == v:
                    yield pre_link, link, var
                else:
                    yield from link_dict_keyval(key, value, v, var, link)
        elif isinstance(var, (list, tuple, set)):
            for d in var:
                yield from link_dict_keyval(key, value, d, var, link)

    # get table link by val
    @staticmethod
    def link_dict_val(val, var, link, pre_link=None):
        if isinstance(var, dict):
            for k, v in var.items():
                if v == val:
                    yield link, var, k
                else:
                    yield from link_dict_val(val, v, var, link)
        elif isinstance(var, (list, tuple, set)):
            for d in var:
                yield from link_dict_val(val, d, var, link)
        else:
            if val == var:
                yield pre_link, link, val

    # table link by key
    @staticmethod
    def link_dict_key(key, var, link, pre_link):
        if isinstance(var, dict):
            for k, v in var.items():
                if k == key:
                    yield link, var, v
                else:
                    yield from link_dict_key(key, v, var, link)
        elif isinstance(var, (list, tuple, set)):
            for d in var:
                yield from link_dict_key(key, d, var, link)

    def by_key_val(self, key, value, data, pre_link=None):

        return_data = []

        op = self.link_dict_key_val(key, value, data, data, pre_link)
        while True:
            try:
                pre_link, link, var = next(op)
                return_data.append(LinkData(pre_link, link, var))
            except StopIteration:
                break

        return return_data

    def by_val(self, value, data, pre_link=None):

        return_data = []

        op = self.link_dict_val(value, data, data, pre_link)
        while True:
            try:
                pre_link, link, key = next(op)
                return_data.append(LinkData(pre_link, link, key))
            except StopIteration:
                break

        return return_data

    def by_key(self, key, data, pre_link=None):

        return_data = []

        op = self.link_dict_key(key, data, data, pre_link)
        while True:
            try:
                pre_link, link, value = next(op)
                return_data.append(LinkData(pre_link, link, value))
            except StopIteration:
                break

        return return_data
