try:
    import ujson as json
except ImportError:
    import json


try:
    from log import logger
except ImportError:
    from ..log import logger


class JSONObject:
    def __init__(self, _dict):
        vars(self).update(_dict)

    @staticmethod
    def to_class(
            content_or_dict, encoding='utf8',
    ):

        if isinstance(content_or_dict, (dict, list, tuple, set)):
            return json.loads(
                json.dumps(content_or_dict), object_hook=JSONObject
            )

        if isinstance(content_or_dict, (bytes, bytearray)):
            return json.loads(
                content_or_dict.decode(encoding), object_hook=JSONObject
            )

        logger.info(f'return clean JSONObject')
        return JSONObject('{}')


def json_as_class(resp_text, encoding='utf8'):
    if isinstance(resp_text, (dict, list, tuple)):
        return json.loads(json.dumps(resp_text), object_hook=JSONObject)
    elif not resp_text:
        return json.loads('{}', object_hook=JSONObject)
    else:
        return json.loads(resp_text.decode(encoding), object_hook=JSONObject)


def test_json_class():

    JSONObject.to_class({})
    JSONObject.to_class([])

    text = '''
{
   "size": 1,
   "parse_time_nanoseconds": 22548,
   "cyr": "тест",
   "en": "test",
   "validate": true,
   "empty": false
}'''
    encoding = 'utf8'
    encoded_text = text.encode(encoding)
    cl = JSONObject.to_class(content_or_dict=encoded_text, encoding=encoding)
    
    for key, value in json.loads(text).items():
        assert getattr(cl, key) == value
