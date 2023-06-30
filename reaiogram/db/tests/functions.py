from ..functions import DbFunctions


def test_calc_hash():

    cl = DbFunctions()
    cl.hash_strings = {}
    cl.hash_strings['temp'] = ['info_hash', 'torrent.info_hash']
    cl.hash_strings['torrent'] = ['info_hash']

    class TempCl: pass

    tmp_cl = TempCl()
    torrent_cl = TempCl()

    setattr(torrent_cl, 'info_hash', '2748fbde16e42cdb3de36b6d4cf314a363802909')
    setattr(torrent_cl, 'hash_key', 'torrent')

    setattr(tmp_cl, 'hash_key', 'temp')
    setattr(tmp_cl, 'db_keys',  (
        'info_hash',
        'torrent',
        'message',
        'version',
        'length',
        'begin',
        'resume_data',
    )
            )

    h = cl.calc_hash(
        tmp_cl,
        {
            'length': 1903600,
            'info_hash': '9e5ac113f3c3d2599647aeac86cdd063b49505f5',
            'torrent': torrent_cl,
        }
    )

    logger.info(f'{h=}')
