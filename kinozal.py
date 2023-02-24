#!/usr/bin/env python3

import time
import feedparser
import re
import os
import requests

from bs4 import BeautifulSoup
from io import BytesIO
from dateutil import parser, tz
from urllib.parse import urlencode, quote_plus

import logging as log
import my.tg as logging

from .f import *
from .sql import *
from .tg.tg import *

from my.config import secrets
global kn_headers
TEMP_COOK = secrets.cookie
PROXY = secrets.proxy
TG_CID = secrets.announce_cid

kn_headers = { 'Cookie': TEMP_COOK,
'Referer': 'http://kinozal.tv/top.php',
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.18 Safari/537.36' }

global TTOR
TTOR=dict(http=f'http://{PROXY}',
        https=f'http://{PROXY}')

logging.basicConfig(level=logging.INFO)

def kn_init():
    return
    
def kn_work(_auto_dir):
    
    s = requests.Session()
    
    resp = tg_get_message()
    _host = ''

    for r in resp:

        print(r)
        if isinstance(r, telebot.types.Update):
            print(r.message.text)
            try:
                if r.message.text:
                    _message = r.message.text
                elif r.message.caption:
                    _message = r.message.caption

                print(_message)

                if not _message:
                    tg_send_cid(r.message.from_user.id, 'CHECK SCRIPT not find text\n\n'+str(r.message))
                    print('NOT FIND TEXT')
                    continue

                if _message.startswith('http'):
                    if 'kinozal' in _message:
                        _host = 'kinozal'
                        rk = s.get('http://dl.kinozal.tv/download.php?id='+_message.split('=')[1], headers=kn_headers, proxies=TTOR)

                        with open(_auto_dir+_message.split('=')[1]+'.torrent', 'wb') as f:
                            f.write(rk.content)
                            
                        tg_send_cid(r.message.from_user.id, 'KINOZAL: '+str(_message))
                    else:
                        tg_send_cid(r.message.from_user.id, 'no kinozal in single link: '+str(_message))

                else:
                    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', _message)
                    for url in urls:
                        try:
                            if 'kinozal' in url:
                                _host = 'kinozal'
                                rk = s.get('http://dl.kinozal.tv/download.php?id='+url.split('=')[1], headers=kn_headers, proxies=TTOR)

                                with open(_auto_dir+url.split('=')[1]+'.torrent', 'wb') as f:
                                    f.write(rk.content)
                                tg_send_cid(r.message.from_user.id, 'KINOZAL: '+str(_message))
                            else:
                                tg_send_cid(r.message.from_user.id, 'no kinozal loop link: '+str(_message))

                        except:
                            logging.debug('urls_loop:\n'+_message+'\n'+urls, exc_info=True, stack_info=True)

            except:
                logging.debug('test', exc_info=True, stack_info=True)
                tg_send_cid(r.message.from_user.id, 'NOT ADD: '+str(_message))

   
def kn_anounce(_torrent, _name):
    tg_send_cid_html(TG_CID, +str(_torrent)+' '+str(_name))

def main_kinozal_releases():
    in_list = set()

    cur_year = int(time.strftime('%Y'))
    p_year = cur_year - 1
    pp_year = p_year - 1
    ppp_year = pp_year - 1

    print('tmain')
    for page in range(0, 10):
    #for page in range(0, 25):
        loop = True
        while loop:
            try:
                resp = requests.get(
                        f'https://kinozal.tv/browse.php?c=1002&page={page}',
                        #'http://kinozal.tv/browse.php?'+urlencode({ 's': _flm })+'&g=0&c=1002&v=0&d='+str(y)+'&w=0&t=0&f=0',
                        headers={ 'Cookie': kn_headers['Cookie'] },
                        proxies=TTOR)
                print('tt')
                loop = False
            except:
                logging.info(f'stack', exc_info=True, stack_info=True)
                time.sleep(10)
                loop = True

        soup = BeautifulSoup(resp.content.decode('cp1251'), 'lxml')
        lines = soup.findAll('td', { 'class': 'nam' })
        for line in lines:
            name = line.text
            href = line.find('a').get('href')
            link = f'https://kinozal.tv{href}'

            print(f'{name=}, {href=}')

            for y_f in [ pp_year, p_year, cur_year ]:
                y_file = 'files/'+str(y_f)+'.txt'

                if not os.path.isfile(y_file):
                    continue

                with open(y_file, 'r') as _f:
                    y_list = _f.readlines()

                for _tflm in y_list:
                    _flm = _tflm.splitlines()[0]
                    _flm = f'{_flm}'
                    
                    if not re.search(f'{re.escape(_flm)}.*{y_f}', name):
                        continue

                    in_list.add(_tflm)
                    break

    logging.info(f'{in_list=}')
    if in_list:
        deep_kinozal_releases(in_list)


def deep_kinozal_releases(in_list=None):
    print('deep')

    db_write = False

    cur_year = int(time.strftime('%Y'))
    p_year = cur_year - 1
    pp_year = p_year - 1
    ppp_year = pp_year - 1
    
    for y_f in [ pp_year, p_year, cur_year ]:
        y_file = 'files/'+str(y_f)+'.txt'

        if not os.path.isfile(y_file):
            continue
        
        if in_list:
            y_list = list(in_list)
        else:
            with open(y_file, 'r') as _f:
                y_list = _f.readlines()

        for _tflm in y_list:
            _flm = _tflm.splitlines()[0]
            _flm = f'{_flm}'

            for y in ppp_year, pp_year, p_year, cur_year:
    
                loop = True
                while loop:
                    try:
                        resp = requests.get('http://kinozal.tv/browse.php?'+urlencode({ 's': _flm })+'&g=0&c=1002&v=0&d='+str(y)+'&w=0&t=0&f=0', headers={ 'Cookie': kn_headers['Cookie'] }, proxies=TTOR)
                        loop = False
                    except:
                        time.sleep(10)
                        loop = True
                print(1)

                with open('search.html', 'wb') as ff:
                    ff.write(resp.content)
                    _utf_html = resp.content.decode('cp1251')
                try:
                    count = int(re.findall('</span>Найдено (.*?) ', _utf_html)[0])
                except:
                    print('except1')
                    continue

                if count == 0:
                    print(_flm+':'+str(y)+': NO RESULT')
                    time.sleep(1)
                    continue

                soup = BeautifulSoup(_utf_html, 'lxml')

                href = soup.findAll('td',  { 'class': 'nam' })
                for hr in href:
                    full_title = hr.text
                    small_title = '/'.join(full_title.split('/')[:4])
                    
                    details = hr.find('a').get('href')
                    pid = details.split('=')[-1]
                    
                    title = full_title.split('/')[0] + ':'
                    title = title.replace(' :', '')

                    btitle = ':' + full_title.split('/')[1] + ':'
                    btitle = btitle.replace(' :', '').replace(': ','')

                    year = full_title.split('/')[2].split(' ')[1]

                    if 'РУ' in year or '-' in year:
                        print(_flm+':'+str(y)+': RU')
                        continue
                    try:
                        year = int(year)
                    except:
                        print('STACK')
                        year = 2018
                    
                    if year < pp_year:
                        continue
                    try:
                        qual = ':' + full_title.split('/')[4]
                    except:
                        print('check127: '+details+'|'+_flm)
                        continue

                    qual = qual.replace(': ','')
                    try:
                        tr = full_title.split('/')[3]
                    except:
                        print('check127: '+details+'|'+_flm)
                        continue
                    tr = tr.replace(' ','')

                    if os.path.isfile('all_db.txt'):
                        if title in open('all_db.txt', ).read():
                            print('existsGLOBALDB: '+full_title)
                            break
                    if small_title in open('all.txt', 'r').read():
                        if 'дб' in tr.lower():
                            print('existsDB: '+title)
                            with open('all_db.txt', fwa('all_db.txt')) as ff:
                                ff.write(full_title+'|'+details+'\n')
                                continue
                        else:
                            print('exists: '+title)
                            continue

                    if 'WEB-DL' in qual or 'BDRip' in qual or 'HDRip' in qual or 'DVDRip' in qual:
                        print('work: '+full_title+' |'+details+'|'+str(year)+'|'+qual)
                        print('http://kinozal.tv'+details)
                        loop = True
                        while loop:
                            try:
                                presp = requests.get('http://kinozal.tv'+details, headers={ 'Cookie': kn_headers['Cookie']  }, proxies=TTOR, allow_redirects=True)
                                loop = False
                            except:
                                time.sleep(10)
                                loop = True

                        with open('p.html', 'wb') as fff:
                            fff.write(presp.content)
                        _t = presp.content.decode('cp1251')
                        #with open('p.html', 'rb') as fff:
                        #    _t = fff.read().decode('cp1251')

                        psoup = BeautifulSoup(_t, 'lxml')
                        
                        desc = psoup.find('p').text
                        extra_desc = r''
                        try:
                            print(psoup.findAll('div', { "class": "bx1 justify" } ))
                            t_extra_desc = psoup.findAll('div', { "class": "bx1 justify" } )
                            for t_ext in t_extra_desc:
                                extra_desc = extra_desc + t_ext.text + '\n\n'
                        except:
                            logging.debug('EXTRA_DESC FAIL '+details, exc_info=True, stack_info=True)
                        
                        try:
                            relisb = psoup.find('div', { 'class': 'pad0x0x5x0' }).find('ul', { 'class': 'lis' })


                            for rl in relisb:
                                if 'релиз' in rl.text.lower():
                                    rlid = rl.get('id').replace('tbch','')
                        except:
                            relisb = []
                            rlid = 'NO_RLID'
                            logging.debug('relisb FAIL '+details, exc_info=True, stack_info=True)
                        
                        print('http://kinozal.tv/get_srv_details.php?id='+pid+'&pagesd='+rlid)
                        loop = True
                        while loop:
                            try:
                                rresp = requests.get('http://kinozal.tv/get_srv_details.php?id='+pid+'&pagesd='+rlid, headers={ 'Cookie': kn_headers['Cookie'] }, proxies=TTOR)
                                loop = False
                            except:
                                time.sleep(10)
                                loop = True

                        imge = True
                        try:
                            img = psoup.find('img', { 'class': 'p200' }).get('src')
                        except:
                            imge = False
                            logging.debug('IMG_FAIL '+details, exc_info=True, stack_info=True)
                        
                        tg_send_loop( ( 'http://kinozal.tv'+details,
                            full_title,
                            rresp.text+'\n'+extra_desc, [ False, '' ], [ imge, img ], False ) )

                        with open('all.txt', fwa('all.txt')) as af:
                            af.write(full_title+'|'+details+'\n')

                        if 'дб' in tr.lower():
                            with open('all_db.txt', fwa('all_db.txt')) as ff:
                                ff.write(full_title+'|'+details+'\n')

