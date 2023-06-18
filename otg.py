import telebot
from telebot import types
from telebot import util
from telebot.types import InputMediaPhoto, InputMediaVideo

from bs4 import BeautifulSoup
import os
import urllib.parse
import tempfile
import json
import requests
import hashlib

# from . import handlers
import logging as log
import logging as logging
#import my.tg as logging

from f import *
from sql import *

from config import secrets
global bot
global last_message

last_message = { 99999: [ False, 0, 'json' ] }

global cids
global tg_trash

tg_trash = secrets.tg_trash


def tg_init(_andrey = False):
   
    check_data()
    global rses
    rses = requests.Session()
    global cids
    if not _andrey:
        if os.path.isfile('.chats.ids'):
            with open('.chats.ids', 'r') as f:
                cids = f.readlines()
        else:
            cids = secrets.cids
            print(f'{cids=}')
    else:
        if os.path.isfile('.chatsA.ids'):
            with open('.chatsA.ids', 'r') as f:
                cids = f.readlines()

    #with open('HTTP_API', 'r') as f:
    #    HTTP_API = f.read()
    
    #global bot
    #bot = telebot.TeleBot(HTTP_API)

    #with open('HTTP_API', 'r') as f:
    #HTTP_API = f.read()
    HTTP_API = secrets.http_api

    global bot
    bot = telebot.TeleBot(HTTP_API)

    for _dir in [ 'last_message' ]:
        dircr(_dir)


def tg_update():
    
    _sql = s_sql('data', '*', 'name=:name', { 'name': 'tg_message_id' })
    try:
        resp = bot.get_updates(_sql[1]+1, 50, 0)
    except:
        logging.info(f'except_gpt', stack_info=True, exc_info=True)
        resp = bot.get_updates(0, 50, 0)
    
    logging.info(f'{resp}')
    try:
        if isinstance(resp[0], telebot.types.Update):
            resp = resp[0]
            print(resp)
            #print(resp.message.from_user)
            u_sql('data', 'tg_message_id', [ { 'name=:name', 'int=:int', 'text=:text', 'date=:date' },
                { 'name': 'tg_message_id', 'int': resp.update_id, 'text': str(resp.update_id), 'date': resp.message.date} ] )

            i_sql('tmp', '(:type, :name, :body, :date, :hdate)', { 'type': 'message', 
                                                            'name': str(resp.message.chat)+' '+str(resp.message.from_user), 
                                                            'body': resp.message.text,  'date': resp.message.date} )
            sql_commit()
    except:
        logging.info(f'except', stack_info=True, exc_info=True)
        npd = 1

def tg_get_message():
    
    _sql = s_sql('data', '*', 'name=:name', { 'name': 'tg_message_id' })
    resp = bot.get_updates(_sql[1]+1, 50, 0)
    _u = False
    for rs in resp:
        _u = True
        
        i_sql('tmp', '(:type, :name, :body, :date, :hdate)', { 'type': 'message', 
            'name': str(rs.message.chat)+' '+str(rs.message.from_user), 
            'body': rs.message.text,  'date': rs.message.date} )

        upd_id = rs.update_id
        mes_date = rs.message.date

    if _u:
        u_sql('data', 'tg_message_id', [ { 'name=:name', 'int=:int', 'text=:text', 'date=:date' },
        { 'name': 'tg_message_id', 'int': upd_id, 'text': str(upd_id), 'date': mes_date} ] )
        
        sql_commit()
    return resp

def ctup(_tup, _num, _var):
    _t = list(_tup)
    _t[_num] = _var
    return tuple(_t)

def tg_prepare_text(_pr_text):
    
    soup = BeautifulSoup(_pr_text[2], 'lxml')
    _pr_text[2] = ''.join(soup.findAll(text=True))

    return _pr_text

def tg_send_cid(_cid, _stext):
    try:
    #if True:
        resp = bot.send_message(_cid, _stext[0:4095], disable_web_page_preview=True)
        return resp
    except:
        log.debug('tg_send_cid:debug: '+str(_cid)+' '+_stext, exc_info=True, stack_info=True)

def tg_resp_parser(_resp):

    #print('TEST:　_resp')
    #print(_resp)
    return
    if isinstance(_resp, telebot.types.Message):
        print('OK')
    else:
        data = json.loads(_resp)
        print(data)
        print(data['ok'])

def parse_last_message(_resp):
    #dircr(str(_resp.chat.id))
    #print(_resp)

    if isinstance(_resp, list):
        _resp = _resp[-1]

    message_id = _resp.message_id
    last_message = { int(_resp.chat.id): [ True,  message_id, 'TEST' ] }
    if os.path.isfile('last_message/'+str(_resp.chat.id)):
        with open('last_message/'+str(_resp.chat.id), 'r') as fr:
            _rmess = fr.read()
        print(_rmess)
        print(message_id)
        if '[0-9]' in _rmess:
            if int(_rmess) < int(message_id):
                with open('last_message/'+str(_resp.chat.id), 'w') as fw:
                    fw.write(str(message_id))
                with open('last_message/'+str(_resp.chat.id)+'.text', 'w') as fw:
                    fw.write(str(_resp.text))
        else:
            with open('last_message/'+str(_resp.chat.id), 'w') as fw:
                fw.write(str(message_id))
            with open('last_message/'+str(_resp.chat.id)+'.text', 'w') as fw:
                fw.write(str(_resp.text))
    else:
        with open('last_message/'+str(_resp.chat.id), 'w') as fw:
            fw.write(str(message_id))
        with open('last_message/'+str(_resp.chat.id)+'.text', 'w') as fw:
            fw.write(str(_resp.text))
    return

def get_last_message(_cid):
    _cid = str(_cid)
    if os.path.isfile('last_message/'+_cid):
        with open('last_message/'+_cid, 'r') as fr:
            _msg_id = int(fr.read())
        with open('last_message/'+_cid+'.text', 'r') as fr:
            _msg_text = fr.read()
            return [ True, _msg_id, _msg_text]
    return [ False, 0 ]

def tg_edit_message_text(text, chat_id=None, message_id=None, inline_message_id=None, parse_mode=None,
                          disable_web_page_preview=None, reply_markup=None):

    print(text)
    print(type(text))
    if text:
        print('is text')
    else:
        print('no text')

    if text:
        _ret = bot.edit_message_text(text, chat_id=chat_id, message_id=message_id,
                inline_message_id=inline_message_id,
                parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview,
                reply_markup=reply_markup)
        if not type(_ret) == bool:
            parse_last_message(_ret)
            
        return _ret

def tg_send_cid_html(_cid, _stext, reply_to_message_id=None, reply_markup=None, 
        disable_web_page_preview=True, disable_notification=None, parse_mode=None,
        _debug=''):
    resp = []
    
    try:
    #if True:
        splitted_text = util.split_string(_stext, 4000)
        for _text in splitted_text:

            resp.append(bot.send_message(_cid, _text, reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification,
                    parse_mode=parse_mode))
            parse_last_message(resp[-1])

            tg_resp_parser(resp)
            time.sleep(0.5)
        return resp

    except telebot.apihelper.ApiException as exc_api:
        zzz = str(exc_api).splitlines()[-1].replace('[','').replace(']','').replace('b\'','').replace('\'','')
        print('tg ApiException')
        print(exc_api)
        dd = json.loads(zzz)
        if dd["error_code"] == 429:

            if 'retry_after' in dd.get('parameters'):
                print('sleep '+str(dd['parameters']['retry_after']))
                _get = get_last_message(_cid)
                print(_get)

                if _get[0]:
                    for i in range(1,dd['parameters']['retry_after']+5):
                        time.sleep(1)
                        tg_edit_message_text('Wait: '+str(i)+'/'+str(dd['parameters']['retry_after']+5), chat_id=_cid, message_id=_get[1])
                    tg_edit_message_text(_get[2], chat_id=_cid, message_id=_get[1])
                else:
                    time.sleep(dd['parameters']['retry_after']+5)

                try:
                    splitted_text = util.split_string(_stext, 4000)
                    for _text in splitted_text:

                        resp.append(bot.send_message(_cid, _text, reply_to_message_id=reply_to_message_id,
                            reply_markup=reply_markup,
                            disable_web_page_preview=disable_web_page_preview,
                            disable_notification=disable_notification,
                            parse_mode=parse_mode))
                        parse_last_message(resp[-1])

                        tg_resp_parser(resp)
                        time.sleep(0.5)
                    return resp
                except:
                    print('tg_send_cid:debug2: '+str(_cid)+' '+str(_stext)+'\n\n'+str(exc_api)+'\n\n'+_debug)
                    log.debug('tg_send_cid:debug2: '+str(_cid)+' '+str(_stext)+'\n\n'+str(exc_api)+'\n\n'+_debug, exc_info=True, stack_info=True)
            else:
                print('tg_send_cid:unknow parameters: '+str(_cid)+' '+str(_stext)+'\n\n'+str(exc_api)+'\n\n'+_debug)
                log.debug('tg_send_cid:unknow parameters: '+str(_cid)+' '+str(_stext)+'\n\n'+str(exc_api)+'\n\n'+_debug, exc_info=True, stack_info=True)
        else:
            print('dd unknow ' + str(zzz) + ' ' + str(exc_api) + ' ' + str(dd))
            logging.debug('dd unknow ' + str(zzz) + ' ' + str(exc_api) + ' ' + str(dd))

    except:
        print('tg_send_cid:debug: '+str(_cid)+' '+str(_stext)+'\n\n'+_debug)
        log.debug('tg_send_cid:debug: '+str(_cid)+' '+str(_stext)+'\n\n'+_debug, exc_info=True, stack_info=True)

def tg_send_cid_htmll(_cid, _stext, reply_to_message_id=None, reply_markup=None, 
        disable_web_page_preview=True, disable_notification=None):
#    try:

    if True:
        _flen = 0
        _send = []
        _split = False
        resp = r''
        _extxt = True

    #if True:
        for _lstr in _stext:
            #print(_lstr)
            _flen += len(_lstr)
            _send.append(_lstr)
            _extxt = True
            #print(_flen)
            if _flen > 3500:
                #print(''.join(_send))
                resp += str(bot.send_message(_cid, ''.join(_send), disable_web_page_preview=disable_web_page_preview, parse_mode="HTML", reply_markup=reply_markup))
                time.sleep(0.5)

                _send = []
                _flen = 0
                _split = True
                _extxt = False

                continue
        print('_extxt:'+str(_extxt))
        if _extxt:
            #print(''.join(_send))
            resp += str(bot.send_message(_cid, ''.join(_send), disable_web_page_preview=True, parse_mode="HTML", reply_markup=reply_markup))
    
    return '123'
#    except:
#        log.debug('tg_send_cid:debug: '+str(_cid)+' '+_stext, exc_info=True, stack_info=True)

def tg_safe_file_mdid(_filename, _filetgid):

    _md5 = hashlib.md5(open(_filename,'rb').read()).hexdigest()

    if os.path.isfile('.tg_files'):
        with open('.tg_files', 'a') as fidd:
            fidd.write(_filename+'|'+_md5+'|'+_filetgid+'\n')
    else:
        with open('.tg_files', 'w') as fidd:
            fidd.write(_filename+'|'+_md5+'|'+_filetgid+'\n')

def tg_check_file_mdid(_filename):

    _rttg = [ False, _filename ]
    _md5cur = hashlib.md5(open(_filename,'rb').read()).hexdigest()

    if os.path.isfile('.tg_files'):
        with open('.tg_files', 'r') as ftgf:
            
            for _line in reversed(ftgf.readlines()):
                line = _line.splitlines()[0]
                if _md5cur in line:
                    _id = line.split('|')[-1]
                    _rttg = [ True, _id ]
                    break

    else:
        _rttg = [ False, _filename ]

    return _rttg

def tg_send_media(
        _cid, _imgl, _caption, parse_mode=None,
        disable_notification=True, reply_to_message_id=None,
        reply_markup=None, media=None,
        _debug='',
        duration=None, width=None, height=None,
        performer=None, title=None):
    resp = []

    _command = str(_cid) + str(_imgl) + str(_caption) + str(media) + str(_debug)
    
    try:
        if media == 'photo' or media == 'image':
            resp.append(
                bot.send_photo(
                    _cid, _imgl, caption=_caption[0:199],
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup
                ))
            if _caption:
                parse_last_message(resp[-1])

        elif media == 'document':
            resp.append(
                bot.send_document(
                    _cid, _imgl, caption=_caption[0:199],
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup
                ))
            if _caption:
                parse_last_message(resp[-1])

        elif media == 'album':

            alb_send = []
            alb_send_ids = []
            if _imgl[1] == 'file':
                for _n, _file in enumerate(_imgl[2]):
                    
                    _check_md5 = tg_check_file_mdid(_file)
                    if _check_md5[0]:
                        _main_photo_id = _check_md5[1]
                        alb_send.append(
                            InputMediaPhoto(
                                _main_photo_id,
                                caption=_caption if _n == 0 else None,
                            )
                        )
                        alb_send_ids.append(_main_photo_id)
                        continue

                    file_size = 0
                    _main_photo_id = None
                    with open(_file, 'rb') as frb:
                        global tg_trash
                        _t = tg_send_media(tg_trash, frb, '', media='photo')
                        if not _t:
                            return

                        for item in _t:
                            for ph in item.photo:
                                if ph.file_size >= file_size:
                                    _main_photo_id = ph.file_id
                                    file_size = ph.file_size

                    if not _main_photo_id == None:
                        tg_safe_file_mdid(_file, _main_photo_id)
                        alb_send.append(
                            InputMediaPhoto(
                                _main_photo_id,
                                caption=_caption if _n == 0 else None,
                            )
                        )
                        alb_send_ids.append(_main_photo_id)

            print(alb_send)
            print(alb_send_ids)
            resp.append(
                bot.send_media_group(
                    _cid, alb_send,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,

                )
                        )

            if _caption:
                parse_last_message(resp[-1])

        elif media == 'video':
            resp.append(bot.send_video(_cid, _imgl, caption=_caption[0:199],
                    duration=duration,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup))
            if _caption:
                parse_last_message(resp[-1])

        elif media == 'audio':
            resp.append(bot.send_audio(_cid, _imgl, caption=_caption[0:199],
                    duration=duration,
                    performer=performer,
                    title=title,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup))
            if _caption:
                parse_last_message(resp[-1])

        else:
            print('tg_send_media:debug unknow media type: '+str(_cid)+' '+media+' '+str(_imgl)+'\n\n'+_debug)
            logging.debug('tg_send_media:debug unknow media type: '+str(_cid)+' '+media+' '+str(_imgl)+'\n\n'+_debug, exc_info=True, stack_info=True)

        return resp
    except telebot.apihelper.ApiException as exc_api:
        zzz = str(exc_api).splitlines()[-1].replace('[','').replace(']','').replace('b\'','').replace('\'','')
        # print(exc_api)
        try:
            dd = json.loads(zzz)
            if dd["error_code"] == 429:

                if 'retry_after' in dd.get('parameters'):
                    print('sleep '+str(dd['parameters']['retry_after']))
                    _get = get_last_message(_cid)
                    print(_get)
            
                    if _get[0]:
                        for i in range(1,dd['parameters']['retry_after']+5):
                            time.sleep(1)
                            tg_edit_message_text('Wait: '+str(i)+'/'+str(dd['parameters']['retry_after']+5), chat_id=_cid, message_id=_get[1])
                        tg_edit_message_text(_get[2], chat_id=_cid, message_id=_get[1])
                    else:
                        time.sleep(dd['parameters']['retry_after']+5)
                
                    try:
                        if media == 'photo' or media == 'image':
                            resp.append(bot.send_photo(_cid, _imgl, caption=_caption[0:199],
                                disable_notification=disable_notification,
                                reply_to_message_id=reply_to_message_id,
                                reply_markup=reply_markup ))
                            parse_last_message(resp[-1])

                        elif media == 'video':
                            resp.append(bot.send_video(_cid, _imgl, caption=_caption[0:199],
                                duration=duration,
                                disable_notification=disable_notification,
                                reply_to_message_id=reply_to_message_id,
                                reply_markup=reply_markup))
                            parse_last_message(resp[-1])

                        elif media == 'audio':
                            resp.append(bot.send_audio(cid, photo, caption=_caption[0:199],
                                duration=duration,
                                performer=performer,
                                title=title,
                                disable_notification=disable_notification,
                                reply_to_message_id=reply_to_message_id,
                                reply_markup=reply_markup))
                            parse_last_message(resp[-1])

                        else:
                            print('tg_send_media:debug unknow media type: '+str(_cid)+' '+str(_imgl)+'\n\n'+_debug)
                            logging.debug('tg_send_media:debug unknow media type: '+str(_cid)+' '+str(_imgl)+'\n\n'+_debug, exc_info=True, stack_info=True)

                        return resp
                    except:
                        print('tg_send_media:debug2: '+str(_cid)+' '+str(_imgl)+'\n\n'+str(exc_api)+'\n\n'+_debug)
                        logging.debug('tg_send_media:debug2: '+str(_cid)+' '+str(_imgl)+'\n\n'+str(exc_api)+'\n\n'+_debug, exc_info=True, stack_info=True)
                else:
                    print('tg_send_media:unknow parameters: '+str(_cid)+' '+str(_imgl)+'\n\n'+str(exc_api)+'\n\n'+_debug)
                    logging.debug('tg_send_media:unknow parameters: '+str(_cid)+' '+str(_imgl)+'\n\n'+str(exc_api)+'\n\n'+_debug, exc_info=True, stack_info=True)
            else:
                print('dd unknow ' +_command+'\n\n' + str(zzz) + ' ' + str(exc_api) + ' ' + str(dd))
                logging.debug('dd unknow ' +_command+'\n\n' + str(zzz) + ' ' + str(exc_api) + ' ' + str(dd))
    
        except:
            try:
                print('tg_send_media:debug: tg get error response from tg servers '+_command+'\n\n'+str(_cid)+' '+str(_imgl)+'\n\n'+_debug)
                logging.debug('tg_send_media:debug: tg get error response from tg servers '+_command+'\n\n'+str(_cid)+' '+str(_imgl)+'\n\n'+_debug, exc_info=True, stack_info=True)
            except:
                log.debug('tg_send_media:debug '+str(_cid)+' '+str(_imgl)+'\n\n'+_debug, exc_info=True, stack_info=True)

def tg_send_loop(text):

    global img
    img = [ False, '' ]
    _text = text
    
    _work_text = list(_text)

    # print(_work_text[4])
    if f'{_work_text[4][1]}' == 'file':
        pass
        img = _work_text[4]
    else:
        if _work_text[4][0] and not _work_text[4][1] == None:
            img = get_img(_work_text[4][1])
        if not img[0]:
            img = search_img(_work_text[2])
            print('after search_img')
        else:
            print('after get_img')
        print('img -> ' + str(img))

    ''' remove tags from text'''
    _work_text = tg_prepare_text(_work_text)

    if img[0]:
        _caption = _work_text[1]+'\n'+tiny_url(_work_text[0])
        _send_text = _work_text[2]

        #if isinstance(img[1], list):
        if f'{img[1]}' == 'file':
            pass
        else:
            photo = open('1.jpg', 'rb')

        for _cid in cids:
            cid = _cid.splitlines()[0]
            
#            try:
#             print(f'{img=}')
#             if isinstance(img[1], list):
            if f'{img[1]}' == 'file':
                t = tg_send_media(
                    cid, img, _caption, media='album',
                    _debug=str(img)+' '+str(text)
                )
                if not t:
                    img[1] = 'other_way'
                    try:
                        photo = open(img[2][0], 'rb')
                        tg_send_media(
                            cid, photo, _caption, media='image',
                            _debug=str(img)+' '+str(text)
                        )
                    except Exception:
                        pass

            else:
                tg_send_media(
                    cid, photo, _caption, media=img[1],
                    _debug=str(img)+' '+str(text)
                )
            
            #if img[1] == 'image':
            #    tg_send_photo(cid, photo, _caption, _debug=str(img)+' '+str(text))
            #elif img[1] == 'video':
            #    resp = bot.send_video(cid, photo, caption=_caption[0:199])
            #elif img[1] == 'audio':
            #    try:
            #        resp = bot.send_audio(cid, photo, caption=_caption[0:199])
            #    except:
            #        logging.debug('_tg_audio_send: ', exc_info=True)
            
            #else:
            #    logging.debug('send_photo_video:' + str(img), exc_info=True)
#            except:
            #    _send_text = _work_text[1]+'\n'+tiny_url(_work_text[0])+'\n'+_work_text[2]
            #    print('img_caption fix')
            #    logging.debug('img_caption fix ' + str(_work_text)+'\n', exc_info=True)
            if f'{img[1]}' == 'file':
                pass
            else:
                photo.seek(0)

        # if isinstance(img[1], list):
        if f'{img[1]}' == 'file':
            pass
        else:
            photo.close()
    else:
        _send_text = _work_text[1]+'\n'+tiny_url(_work_text[0])+'\n'+_work_text[2]

    if not _work_text[5]:
        for _cid in cids:
            cid = _cid.splitlines()[0]
        
            try: resp = bot.send_message(cid, _send_text[0:4095], disable_web_page_preview=True)
            except Exception as ex:
                if not _work_text[5] and not img[0]:
                    print('text cant send fix')
                    logging.debug('text cant send fix ' + str(_work_text)+'\n\n'+str(ex), exc_info=True, stack_info=True)




def tg_send_loop_new(text):

    global img
    _media_to_send = [ False, [] ]
    img = [ False, '' ]
    _text = text
    
    _work_text = list(_text)

    if _work_text[4][0] and not _work_text[4][1]:
        img = get_img(_work_text[4][2][0])
    if not img[0]:
        img = search_img(_work_text[2])
        print('after search_img')
    else:
        print('after get_img')
    print('img -> ' + str(img))


    ''' remove tags from text'''
    _work_text = tg_prepare_text(_work_text)

    if img[0]:
        _caption = _work_text[1]+'\n'+tiny_url(_work_text[0])
        _send_text = _work_text[2]

        photo = open('1.jpg', 'rb')

    for _cid in cids:
        cid = _cid.splitlines()[0]
        
        if _work_text[4][1]:
            # album
            for albs in _work_text[4][2]:
                tg_send_media(cid , [ True, 'file' , albs], False, media='album')
        
        elif img[0]:
            tg_send_media(cid, photo, _caption, media=img[1], _debug=str(img)+' '+str(text))
            photo.seek(0)

    if img[0]:
        photo.close()
    elif _work_text[4][1]:
        _send_text = _work_text[1]+'\n'+tiny_url(_work_text[0])+'\n'+_work_text[2]
        #_send_text = tiny_url(_work_text[0])+'\n'+_work_text[1]+'\n'+_work_text[2]
    elif img[0] and not _work_text[4][1]:
        _send_text = _work_text[1]+'\n'+tiny_url(_work_text[0])+'\n'+_work_text[2]
        #_send_text = tiny_url(_work_text[0])+'\n'+_work_text[1]+'\n'+_work_text[2]

    if not _work_text[5]:
        for _cid in cids:
            cid = _cid.splitlines()[0]
        
            try: resp = bot.send_message(cid, _send_text[0:4095], disable_web_page_preview=True)
            except Exception as ex:
                if not _work_text[5] and not img[0]:
                    print('text cant send fix')
                    logging.debug('text cant send fix ' + str(_work_text)+'\n\n'+str(ex), exc_info=True, stack_info=True)

