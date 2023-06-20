import string
import random

from base64 import b64encode


def create_ref_key(string_length=15, letters=string.ascii_letters):
    """Generate a random string of fixed length """
    return b64encode(
        (''.join(random.choice(letters) for i in range(string_length)).encode(
            'utf8'))).decode('utf8')
