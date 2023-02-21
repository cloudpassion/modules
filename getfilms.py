#!/usr/bin/env python3

import time
import feedparser
import re
import os
import requests
import json
from io import BytesIO
from dateutil import parser, tz
from bs4 import BeautifulSoup
from .f import *
from .sql import *
from .tg import *
''' get date string from post, maybe in updated or published var (atom or rss type of rss)'''


from my.config import secrets
PROXY = secrets.proxy

global TTOR
TTOR=dict(http=f'socks5://{PROXY}',
        https=f'socks5://{PROXY}')

global global_films, global_tfilms
global_films = set()
global_tfilms = []

def get_upcoming_imdb():
    
    entries = []
    for region in ['US', 'RU', 'UA', ]:
    #for region in ['US', ]:
        for tp in ['MOVIE', 'TV', ]:
        #for tp in ['MOVIE', ]:
            link = f'https://www.imdb.com/calendar/?ref_=rlm&region={region}&type={tp}'
    
            resp = requests.get(
                    link,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
                        }
                    )

            #with open('get_temp.html', 'wb') as hw:
            #    hw.write(resp.content)

            text = resp.content.decode('utf8')

            soup = BeautifulSoup(text, 'lxml')
            
            main = soup.find('script', {'id': '__NEXT_DATA__'})
            groups = json.loads(main.text).get('props').get('pageProps').get('groups')
    
            for group in groups:
                for entry in group.get('entries'):
                    entries.append(entry)

    for entry in entries:
        title = entry.get('titleText')
        global_tfilms.append(title)

def get_search_imdb(year=2022):

    f'&start=51&ref_=adv_nxt'

    link = f'https://www.imdb.com/search/title/?title_type=feature&release_date={year}-01-01,{year}-12-31&view=simple'
    
    _next = 0

    resp = requests.get(f'{link}&start={_next}&ref_=adv_nxt')
    
    with open('get_temp.html', 'wb') as hw:
        hw.write(resp.content)

    text = resp.content.decode('utf8')
    soup = BeautifulSoup(text, 'lxml')

    _count = soup.find('div', {'class': 'desc'})
    count = int(''.join(re.findall('[0-9]', re.findall(' (.*?) titles', f'{_count}')[0])))
    
    for page in range(0, int(count/50)):
        print(f'{page=}')    
        try:
            main = soup.findAll('a') #, 'href') #v', {'class': 'lister list detail sub-list'})
            
            text = ''
            for a in main:
                text += f'{a}\n'

            titles = re.findall('<a href="/title/.*/">(.*?)</a>', text)

            for title in titles:
                global_tfilms.append(title)

            _next += 50
            resp = requests.get(f'{link}&start={_next}&ref_=adv_nxt')
            text = resp.content.decode('utf8')
            soup = BeautifulSoup(text, 'lxml')

            with open('get_temp.html', 'wb') as hw:
                hw.write(resp.content)

        except Exception as exc:
            logging.info('t', stack_info=True, exc_info=True)
            print('stack')

        time.sleep(2)

def get_kinopoisk(_year, fromt3=False):
    global global_tfilms

    main_headers = { 'Referer': 'https://www.kinopoisk.ru/premiere/ru/'+_year+'/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.18 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest' }
    main = requests.get('https://www.kinopoisk.ru/premiere/ru/'+_year+'/')

    token = re.findall("var xsrftoken = '(.*?)';", main.text)[0]

    if not fromt3:
        _f = open('t3', 'wb')
        
        for mon in range(1,13):
            for i_page in range(0,12):
                p = requests.post('https://www.kinopoisk.ru/premiere/ru/'+_year+'/month/'+str(mon)+'/', headers=main_headers, data={ 'token': token, 'page': i_page, 'ajax': 'true' })
                print(str(mon)+' '+str(i_page)+' '+str(p.status_code))
                _f.write(p.content)
                time.sleep(5)
        _f.close()
    
    with open('t3', 'rb') as f:
        _fhtml = f.read().decode('utf8')

    _films = re.findall('<span class="name" itemprop="name"><a href=".*?">(.*?)<', _fhtml)

    for _flm in _films:
        _nflm = _flm.lower().replace('–', '-').replace('&nbsp;',' ')
        global_tfilms.append(_nflm)

def get_kinonews():
    global global_tfilms

    main = requests.get('https://www.kinonews.ru/movies_waitings/')

    _films = re.findall('class="titlefilm">(.*?)<', main.content.decode('utf8'))

    for _flm in _films:
        _nflm = _flm.lower().replace('–', '-').replace('&nbsp;',' ')
        global_tfilms.append(_nflm)

def get_kinoafisha(_year):
    global global_tfilms

    main = requests.get('https://www.kinoafisha.info/releases/'+_year+'/')
    
    _films = BeautifulSoup(main.text, 'lxml')
    for _flm in _films.findAll('img', { 'class': 'poster_image'} ):
        
        _nflm = _flm.get('alt').lower().replace('–', '-').replace('&nbsp;',' ')
        global_tfilms.append(_nflm)

def get_kinomania(_year):
    global global_tfilms

    main_headers = { 'Referer': 'http://www.kinomania.ru/list/year/'+_year,
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.18 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest' }

    main = requests.get('http://www.kinomania.ru/list/year/'+_year)

    _films = re.findall('<div class="name"><a href=".*?">(.*?)<', main.text)[:-2]
    
    for _flm in _films:
        _nflm = _flm.lower().replace('–', '-').replace('&nbsp;',' ')
        global_tfilms.append(_nflm)
    
    for i_page in range(2,37):
        p = requests.post('http://www.kinomania.ru/list/year/'+_year+'?handler=getMore&page='+str(i_page), headers=main_headers, data={ 'handler': 'getMore', 'page': i_page })
        print(p.status_code)
        if p.status_code == 404:
            time.sleep(2)
            continue
        _data = json.loads(p.text)
        
        for _flm in _data:
            if _flm.get('name_ru'):
                _nflm = _flm.get('name_ru').lower().replace('–', '-').replace('&nbsp;',' ').replace('«','').replace('»','')
            else:
                _nflm = _flm.get('name_origin').lower().replace('–', '-').replace('&nbsp;',' ').replace('\xa0','').replace('«','').replace('»','')
            global_tfilms.append(_nflm)
        time.sleep(2)

def uniq_list(_in_list):
    seen = set()
    for az in _in_list:
        if az not in seen:
            
            seen.add(az)
    return seen
