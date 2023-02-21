import time
import os
import re
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import urllib.parse

import logging as log
import my.tg as logging

import imghdr, magic
import json

import string
import random

from my.config import secrets
PROXY = secrets.proxy
TG_ADMIN = secrets.tg_admin
TG_TRASH = secrets.tg_trash

global tg_admin
global TTOR
TTOR=dict(http=f'socks5://{PROXY}',
        https=f'socks5://{PROXY}')

tg_admin = TG_ADMIN # log_temp
tg_trash = TG_TRASH # photo_temp

headers = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36",
        }

global frSes
frSes = requests.Session()
frSes.headers.update(headers)
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
frSes.mount('http://', adapter)
frSes.mount('https://', adapter)

def dircr(dname):
    if not os.path.exists(dname):
        os.makedirs(dname)

def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def find_url(_message):
    _Lret = []
    _finded = False
    if _message.startswith('http'):
        return [ True, False, _message ]
    else:
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', _message)
        for url in urls:
            try:
                _Lret.append(url)
                _finded = True
            except:
                logging.debug('urls_loop:'+_message+' '+urls, exc_info=True, stack_info=True)
            return [ False, False, '' ]

    return [ _finded, True, _Lret ]

def tiny_url(_link):
    try:
        #resp = requests.get('https://tinyurl.com/create.php?source=indexpage&url='+
        #        urllib.parse.quote_plus(_link)+'&submit=Make+TinyURL%21&alias=')
        #_tiny_link = re.findall('<div id="copyinfo" data-clipboard-text="(.*?)"', resp.text )
        #print(_tiny_link)
        return _link
        #return _tiny_link[0]
    except:
        return _link

def fwa(_file):
    if os.path.isfile(_file):
        fmode = 'a'
    else:
        fmode = 'w'
    return fmode

def frw(_file):
    if os.path.isfile(_file):
        fmode = 'r'
    else:
        fmode = 'w'
    return fmode

def frwp(_file):
    if os.path.isfile(_file):
        fmode = 'r+'
    else:
        fmode = 'w+'
    return fmode

def tail(f, n, offset=None):
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

def tailf(_f, _n, offset=None):
    _ff = open(_f, 'r')
    _tail = tail(_ff, _n)
    _ff.close()
    
    return(_tail)

def search_img(_in_text):
   
    _is_img = [ False, '' ]
    
    #_spat = re.compile(r'(\.png|\.jpg|\.jpeg|\.bmp|\.gif)')
    #if _spat.search(_in_text) is not None:
    #lnk = re.compile(r'[<img.*?[href|src]="(htt.*?[\.png|\.jpg|\.jpeg|\.bmp])"', re.DOTALL)
    #lnk = re.compile(r'/([^/]+\.(?:jpg|gif|png|jpeg|bmp))')
    lnk = re.compile(r'(?:http\:|https\:)?\/\/.*?\.(?:png|jpg|bmp|jpeg|gif)')
    reddit_lnk = re.compile(r'<span><a href="(.*?)">\[link\]</a>')
    
    if reddit_lnk.search(_in_text):
        try: _tmp_url = re.findall(reddit_lnk, _in_text)[0]
        except: return _is_img

        print('_tmp_urlRED --> ' + str(_tmp_url))
        _is_img = get_img(_tmp_url)
    
    elif lnk.search(_in_text):
        try:
            if re.search('src=', _in_text):
                _in_text = re.findall('src="(.*?)(?: |")', _in_text)[0]
        except:
            try:
                _in_text = re.findall("src='(.*?)(?: |')", _in_text)[0]
            except:
                a = 1
                #logging.debug('FIX_IMGSRC'+_in_text)
            
        try: _in_text = _in_text.split('"')[0]
        except: t = 123
        try: _in_text = _in_text.split(' ')[0]
        except: t = 123
        try: _in_text = _in_text.split("'")[0]
        except: t = 123

        try: _tmp_url = re.findall(lnk, _in_text)[0]
        except: return _is_img
        
        _tmp_url = _tmp_url.replace('habrastorage.org','hsto.org')

        print('_tmp_url2 --> ' + str(_tmp_url))
        _is_img = check_img(_tmp_url)

    return _is_img

def check_img(_link):
    if _link == None:
        return [ False, 'NONE0' ]
    
    if 'http' in _link:
        #try:
        if True:
            try:
                r = frSes.get(_link, allow_redirects=True, timeout=30.0)
            except:
                logging.debug('check_img_1 frSes.get:', exc_info=True, stack_info=True)
                return [ False, 'network' ]

        #except:
        #    logging.debug('check_img_1:', exc_info=True)
            #return [ True, 'SSL_check_img_1' ]
    else:
        try:
            r = frSes.get('http:'+_link, allow_redirects=True, timeout=20.0)
        except:
            try:
                r = frSes.get('https:'+_link, allow_redirects=True, timeout=20.0)
            except:
                logging.debug('check_img_2:', exc_info=True, stack_info=True)
                return [ False, 'SSL_check_img_2' ]

    with open('1.jpg', 'wb') as f_img:
        f_img.write(r.content)
    _check_img = imghdr.what('1.jpg')
    print('_check_img:imghdr ' + _link+ ' ' +str(_check_img))
    if _check_img == None:
        _m = magic.detect_from_filename('1.jpg').mime_type #, mime=True)
        if 'image' in _m:
            print('_check_img:magic:image ' + str(_m))
            _tp = photo_type(str(_m))
            return [ True, _tp ]
        elif 'video' in _m:
            print('_check_img:magic:video '+str(_m))
            return [ True, 'video' ]
        elif 'audio' in _m:
            print('_check_img:magic:video '+str(_m))
            return [ True, 'audio' ]
        elif 'text/html' in _m:
            return [ False, 'text/html' ]
        elif 'text/plain' in _m:
            return [ False, 'text/plain' ]
        else:
            _p = magic.detect_from_filename('1.jpg')
            print(_p)
            if 'Web/P image' in _p:
                return [ True, 'riff webp' ]
            else:
                print('_check_img:magic:unknow '+str(_m)+' '+_link)
                logging.debug('_check_img:unknow: '+str(_m)+' '+_link)

        return [ False, 'NONE1' ]
    else:
        _tp = photo_type(_check_img)
        return [ True, _tp ]

def photo_type(_str):
    if 'png' in _str or 'bmp' in _str or 'jpeg' in _str:
        return 'image'
    elif 'gif' in _str or 'video' in _str:
        return 'video'
    elif _str == 'ready':
        _tph = photo_type(str(magic.detect_from_filename('1.jpg').mime_type)) # , mime=True)))
        return _tph
    else:
        logging.debug('photo_type:unknow: '+_str+' '+_str)
        return 'image'

def get_img(_link):
        img_domain = _link.split('/')[2:3]
        print(_link)
        #_lnk = re.compile(r'[\.png|\.jpg|\.jpeg|\.bmp|\.gif]')
        #_lnk = re.compile(r'/([^/]+\.(?:jpg|gif|png|jpeg|bmp))')
        #_lnl = re.compile(r'(?:http\:|https\:)?\/\/.*\.(?:png|jpg)')

        if re.search('i.redd.it', img_domain[0]):
            return check_img(_link)
        
        elif 'imgur.com' in img_domain[0] and not 'i.imgur.com' in img_domain[0]:
            if 'jpg' in _link or 'png' in _link or 'jpeg' in _link or 'bmp' in _link:
                return check_img(_link)
            r = frSes.get(_link)
            try: return check_img(re.findall('<link rel="image_src".*?href="(.*?)"', r.text)[0])
            except: return [ False, '' ] 
        
        elif re.search('deviantart.com', img_domain[0]):
            r = frSes.get(_link)
            try: return check_img(re.findall('data-super-full-img="(.*?)"', r.text)[0])
            except: return [ False, '' ]
        
        elif re.search('flickr.com', img_domain[0]):
            r = frSes.get(_link)
            try: return check_img(re.findall('<meta property="og:image" content="(.*?)"', r.text)[0])
            except: return [ False, '' ]
        elif re.search('www.reddit.com', img_domain[0]):
            return [ False, '' ]
            #r = requests.get(_link)
            #print(4)
            #return get_img(re.findall('<meta name="description" content="(htt[p|ps]:.*?[\.jpg|\.png|\.jpeg|\.bmp]) ', r.text))[0]
        elif re.search('asciinema.org', img_domain[0]):
            
            r = frSes.get(_link)
            try:
                _asc = re.findall(r'<meta property="og:image" content="(.*?)"', r.text)[0]
            except:
                _asc = None

            return check_img(_asc)
        elif re.search('upload.wikimedia.org', img_domain[0]):
            
            try:
                _wiki = _link+'/1024px-'+_link.split('/')[-1]
            except:
                _wiki = _link
                logging.debug('FIXWIKIGIMG '+_link)

            return check_img(_wiki)

        elif re.search('youtube.com', img_domain[0]) or re.search('youtu.be', img_domain[0]) or re.search('www.youtube.com', img_domain[0]) or re.search('www.youtu.be', img_domain[0]):
            try: _ytb_t = _link.split('v%3D')[1].split('%')[0]
            except: 
                try: _ytb_t = _link.split('v=')[1].split('&')[0]
                except: 
                    try: _ytb_t = _link.split('v=')[1]
                    except:
                        try: _ytb_t = _link.split('/')[-1]
                        except: 
                            logging.debug('FIXYTB_RETURN_FALSE:'+_link)
                            return [ False, '' ]
            try: _ytb_t = _ytb_t.split('?')[0]
            except: logging.debug('FIX:YTB_QUESTION')

            #logging.debug(_ytb_t)
            from my.config import secrets
            YTB_KEY = secrets.tfytvkey
            r = frSes.get('https://www.googleapis.com/youtube/v3/videos?part=snippet&fields=items(id%2Ckind%2Csnippet)&key={}&id={}'.format(YTB_KEY, _ytb_t)).text
            data = json.loads(r)
            _ytb = None
            for resol in 'maxres', 'standard', 'high':
                try:
                    _ytb = data.get('items')[0].get('snippet').get('thumbnails').get(resol).get('url')
                except:
                    continue

                if not _ytb == None:
                    break
            return check_img(_ytb)

        elif re.search('gfycat.com', img_domain[0]):

            if 'detail' in _link:
                _gfy = _link
            elif 'webm' in _link:
                return check_img(_link)
            elif 'thumbs' in _link:
                return check_img(_link)
            else:
                _gfy = 'https://gfycat.com/gifs/detail/'+_link.split('/')[-1]

            r = frSes.get(_gfy).text
            
            giflink = re.findall('"gifUrl":"(.*?'+_link.split('/')[-1]+'.*?\.gif)"', r)[0]
            
            print(giflink)
            giflink = _link.replace('\u002F','/')
            print(giflink)

            return check_img(giflink)

        elif re.search('vimeo.com', img_domain[0]):
            r = frSes.get('https://vimeo.com/api/oembed.json?url='+_link)
            data = json.loads(r.text)
            try:
                _vimeo_thumb = data.get('thumbnail_url')
            except:
                _vimeo_thumb = None
            
            return check_img(_vimeo_thumb)

        elif re.search('coub.com', img_domain[0]):
            r = frSes.get('https://coub.com/api/v2/coubs/'+_link.split('/')[-1]).text
            data = json.loads(r)

            for ver in data.get('image_versions').get('versions'):
                _coub_image = data.get('image_versions').get('template').format(version=ver).replace('%','')
                #logging.debug(_coub_image)
                if ver == 'big':
                    break
            return check_img(_coub_image)
        elif re.search('giphy.com', img_domain[0]):
            try:
                _giphy = 'https://media.giphy.com/media/'+_link.split('/')[-1].split('-')[1]+'/giphy_s.gif'
            except:
                try:
                    _giphy = 'https://media.giphy.com/media/'+_link.split('/')[-1]+'/giphy_s.gif'
                except: return [ False, '' ]
            return check_img(_giphy)

        elif re.search('instagram.com', img_domain[0]):
            r = frSes.get(_link)
            try: return check_img(re.findall('<meta property="og:image" content="(.*?)"', r.text)[0])
            except: return [ False, '' ]
        
#        elif re.search(re.compile(r'http.*?[\.png|\.jpg|\.jpeg|\.bmp|\.gif]'), _link):
        elif re.search(re.compile(r'(?:http\:|https\:)?\/\/.*?\.(?:png|jpg|bmp|jpeg|gif)'), _link):

            try: return check_img(_link)
            except: return [ False, '' ]

        elif re.search(re.compile(r'(?:http\:|https\:)?\/\/.*?\.(?:webm|mp4|avi|mpeg|3gp)'), _link):
            try: return check_img(_link)
            except: return [ False, '' ]
            
        else:
            try: return check_img(_link)
            except:
                logging.debug('fix add link img: ' + _link)
                return [ False, '' ]

def reddit_img(_rtext):
    
    _is_img = False
    _img_href = r''

    lnk = re.compile(r'<span><a href="(.*?)">\[link\]</a>')
    try:
        _img_href = re.findall(lnk, _rtext)[0]
    except AttributeError:
        return [ _is_img, _img_href ]
    
    _tmp_href = get_img(_img_href)
    if _tmp_href is None:
        return [ False, _img_href ]

    _img_href = _tmp_href

    resp = frSes.head(_tmp_href, allow_redirects=True)
    try:
        if 'image' in resp.headers['Content-Type']:
            _is_img = True
            _img_href = resp.url
    except AttributeError:
        _img_href = _tmp_href
        print(resp.headers)
    
    return [ _is_img, _img_href ]
