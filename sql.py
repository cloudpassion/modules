import sqlite3
import time

def check_xml(_xmls, _table):

    commit = False

    for _xml in _xmls:

        xml = _xml.splitlines()[0]
        r = cursor.execute("SELECT url FROM {} WHERE url=:url".format(_table), {'url': xml })

        if r.fetchone() is None:
            cursor.execute("INSERT INTO {} VALUES (:url, :date, :text)".format(_table), {'url': xml, 
                                                                            'date': int(time.strftime('%s', time.gmtime())), 
                                                                            'text': time.strftime('%d.%m.%Y_%H:%M', time.gmtime()) })
            commit = True
    if commit:
        conn.commit()

def check_data2(_table, _vars):
    commit = False
    
    for name in _vars:
        r = cursor.execute("SELECT name FROM {} WHERE name=:name".format(_table), {'name': name })

        if r.fetchone() is None:
            cursor.execute("INSERT INTO {} VALUES (:name, :int, :text, :date, :hdate)".format(_table), {'name': name, 
                                                                            'int': 0,
                                                                            'text' : '0',
                                                                            'date': int(time.strftime('%s', time.gmtime())), 
                                                                            'hdate': time.strftime('%d.%m.%Y_%H:%M', time.gmtime()) })
            commit = True
    if commit:
        conn.commit()

#def check_data3(_table, _var, _data):
#    _data['hdate']=time.strftime('%d.%m.%Y_%H:%M', time.gmtime(_data['date']))
#    r = cursor.execute("INSERT INTO {} VALUES {}".format(_table, _var), _data)
#    return r.fetchone()

def check_data():

    commit = False

    for name in [ 'tg_message_id' , 'fsb_token', 'bot_cookie' ]:

        r = cursor.execute("SELECT name FROM data WHERE name=:name", {'name': name })

        if r.fetchone() is None:
            cursor.execute("INSERT INTO data VALUES (:name, :int, :text, :date, :hdate)", {'name': name, 
                                                                            'int': 0,
                                                                            'text' : '0',
                                                                            'date': int(time.strftime('%s', time.gmtime())), 
                                                                            'hdate': time.strftime('%d.%m.%Y_%H:%M', time.gmtime()) })
            commit = True
    if commit:
        conn.commit()

def sql_sel(_req, _data):
        
        cursor.execute(_req, _data)
        return int(cursor.fetchone()[0])

def sql_commit():
    conn.commit()


def sql_table(_table, *params):
    try:
        _database = params[2]
    except:
        _database = 'rss.sqlite'
    #print('SQLT: '+_database)
    global conn
    global cursor
    
    conn = sqlite3.connect(_database, check_same_thread=False)
    cursor = conn.cursor()

    if params[0]:
        _par = params[1]
    else:
        _par = 'url text, date int, hdate text'

    try:
        cursor.execute('''CREATE TABLE {}
                ({})'''.format(_table, _par))
    except:
        d = 1

def sql_init(_database = 'rss.sqlite'):
    #print('SQL_INIT: '+str(_database))
    global conn
    global cursor
    
    conn = sqlite3.connect(_database, check_same_thread=False)
    cursor = conn.cursor()

# rss
    try:
        cursor.execute('''CREATE TABLE full
                (url text, date int, hdate text)''')
    except:
        d = 1

# vk
    try:
        cursor.execute('''CREATE TABLE vk
                (url text, date int, hdate text)''')
    except:
        d = 1
# fsb
    try:
        cursor.execute('''CREATE TABLE fsb
                (url text, date int, hdate text)''')
    except:
        d = 1

    try:
        cursor.execute('''CREATE TABLE data
                (name text, int int, text text, date int, hdate text)''')
    except:
        d = 1

    try:
        cursor.execute('''CREATE TABLE tmp
                (type text, name text, body text, date int, hdate text)''')
    except:
        d = 1

# cookie
    try:
        cursor.execute('''CREATE TABLE cookies
                (name text, int int, text text, date int, hdate text)''')
    except:
        d = 1

def i_sql(_table, _var, _data):
    _data['hdate']=time.strftime('%d.%m.%Y_%H:%M', time.gmtime(_data['date']))
    r = cursor.execute("INSERT INTO {} VALUES {}".format(_table, _var), _data)
    return r.fetchone()

def i_sqls(_table, _var, _data):
    #_data['hdate']=time.strftime('%d.%m.%Y_%H:%M', time.gmtime(_data['date']))
    r = cursor.execute("INSERT INTO {} VALUES {}".format(_table, _var), _data)
    return r.fetchone()

def s_sql(_table, _var, _val, _data):
    r = cursor.execute("SELECT {} FROM {} WHERE {}".format(_var, _table, _val), _data)
    return r.fetchone()

def s_sqlr(_table, _var, _val, _data):
    r = cursor.execute("SELECT {} FROM {} WHERE {}".format(_var, _table, _val), _data)
    return r.fetchall()

def s_sqll(_table, _par, _var, _val, _dop):
    r = cursor.execute("SELECT "+_par+" FROM "+_table+" WHERE "+_var+" LIKE '%"+_val+"%'"+_dop)

    return r.fetchall()

def s_sqlrt(_table, _var):
    r = cursor.execute("SELECT DISTINCT {} FROM {}".format(_var, _table))
    return r.fetchall()

def s_sqlo(_table, _var, _val, _data, _tes):
    r = cursor.execute("SELECT {} FROM {} WHERE {} ORDER BY {}".format(_var, _table, _val, _tes), _data)
    return r.fetchall()

def u_sql(_table, _point, *_data):
    _data=_data[0]
    #print(_table)
    #print(_point)
    #print(_data)
    #print(', '.join(_data[0]))
    cursor.execute("UPDATE {} SET {} WHERE name=:name".format(_table, ', '.join(_data[0])), _data[1] )
    #{'url': _xml, 
             #                                                              'date': int(_date), 
              #                                                             'hd': time.strftime('%d.%m.%Y_%H:%M', time.gmtime(_date)) }) 
def u_sqls(_table, _point, *_data):
    _data=_data[0]
    #print(_table)
    #print(_point)
    #print(_data)
    #print(', '.join(_data[0]))
    cursor.execute("UPDATE {} SET {} WHERE name=:name".format(_table, ', '.join(_data[0])), _data[1])

def u_test(SQL, clear_row, _data):
#        dic = { 'availQuantity': None, 'bulkOrder': None, 'inventory': None, 'isActivity': None, 'skuBulkCalPrice': None, 'skuCalPrice': None, 'skuDisplayBulkPrice': None, 'skuMultiCurrencyBulkPrice': None, 'skuMultiCurrencyCalPrice': None, 'skuMultiCurrencyDisplayPrice': None, 'skuMultiCurrencyPerPiecePrice': None, 
#            'page_id': None, 'skuPropIds': None, 'skuAttr': None, 'cRUB': None, 'cUSD': None, 'varText': None, 'title': None, 'date': None, 'hdate': None}

#    SQL = "INSERT INTO ali VALUES (:availQuantity, :bulkOrder, :inventory, :isActivity, :skuBulkCalPrice, :skuCalPrice, :skuDisplayBulkPrice, :skuMultiCurrencyBulkPrice, :skuMultiCurrencyCalPrice, :skuMultiCurrencyDisplayPrice, :skuMultiCurrencyPerPiecePrice, :page_id, :skuPropIds, :skuAttr, :cRUB, :cUSD, :varText, :title, :date)"

    cursor.executemany(SQL, ({k: d.get(k, [k]) for k in clear_row} for d in [ _data ]))

#    cursor.executemany('UPDATE ali SET {} WHERE {}:={}'.format(_t, _s, _f), ({k: d.get(k, _tess[k]) for k in _tess} for d in _tess))

def update_sql(_table, _xml, _date):

    cursor.execute("UPDATE {} SET date=:date, hdate=:hd WHERE url=:url".format(_table), {'url': _xml, 
                                                                           'date': int(_date), 
                                                                           'hd': time.strftime('%d.%m.%Y_%H:%M', time.gmtime(_date)) })

def sql_close():
    conn.commit()
    conn.close()
