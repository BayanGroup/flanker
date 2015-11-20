# coding:utf-8
"""
Utility functions and classes used by flanker.
"""
from __future__ import absolute_import
import logging
import re

import chardet as cchardet
import chardet
import six

#from flanker.mime.message import errors
from functools import wraps

from flanker.str_analysis import sta
from six.moves import map
from six.moves import range

log = logging.getLogger(__name__)


def _guess_and_convert(value):
    """
    Try to guess the encoding of the passed value and decode it.

    Uses cchardet to guess the encoding and if guessing or decoding fails, falls
    back to chardet which is much slower.
    """
    sta(value)  # {u'str': 10}
    try:
        return _guess_and_convert_with(value)
    except:
        log.warn("Fallback to chardet")
        return _guess_and_convert_with(value, detector=chardet)


def _guess_and_convert_with(value, detector=cchardet):
    """
    Try to guess the encoding of the passed value with the provided detector
    and decode it.

    The detector is either chardet or cchardet module.
    """
    sta(value)  # {u'str': 11}}
    charset = detector.detect(value)

    if not charset["encoding"]:
        raise Exception("Failed to guess encoding for %s" % (value,))

    try:
        value = value.decode(charset["encoding"], "replace")
        return value

    except (UnicodeError, LookupError) as e:
        raise Exception(str(e))


def _make_unicode(value, charset=None):
    # sta(value)  # OK {u'str': 182, u'str/a': 477, u'uc': 13, u'uc/a': 14}
    if isinstance(value, six.text_type):
        return value

    try:
        # if charset is provided, try decoding with it
        if charset:
            value = value.decode(charset, "strict")

        # if charset is not provided, assume UTF-8
        else:
            value = value.decode("utf-8", "strict")

    # last resort: try to guess the encoding
    except (UnicodeError, LookupError):
        value = _guess_and_convert(value)

    return value


def to_unicode(value, charset=None):
    # sta(value)  # OK {u'str': 49, u'str/a': 80}
    value = _make_unicode(value, charset)
    return six.text_type(value.encode("utf-8", "strict"), "utf-8", "strict")


def to_utf8(value, charset=None):
    '''
    Safely returns a UTF-8 version of a given string
    >>> utils.to_utf8(u'hi')
        'hi'
    '''

    # sta(value)  # OK {u'str/a': 10, u'uc': 13, u'uc/a': 14}
    value = _make_unicode(value, charset)

    return value.encode("utf-8", "strict")


def is_pure_ascii(value):
    '''
    Determines whether the given string is a pure ascii
    string
    >>> utils.is_pure_ascii(u"Cаша")
        False
    >>> utils.is_pure_ascii(u"Alice")
        True
    >>> utils.is_pure_ascii("Alice")
        True
    '''

    sta(value)  # {u'str': 14, u'str/a': 17176, u'uc': 7, u'uc/a': 1}
    if value is None:
        return False
    if not isinstance(value, (six.text_type, six.binary_type)):
        return False
    if isinstance(value, six.binary_type):
        value = value.decode('iso-8859-1')

    try:
        value.encode("ascii")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False
    return True


def cleanup_display_name(name):
    # sta(name)  # OK {u'uc': 84, u'uc/a': 12227}
    if isinstance(name, six.text_type):
        return name.strip(u''';,'\r\n ''')
    else:
        return name.strip(b''';,'\r\n ''')


def cleanup_email(email):
    # sta(email)  # OK {u'str/a': 8246, u'uc/a': 5388}
    if isinstance(email, six.text_type):
        return email.strip(u"<>;, ")
    else:
        return email.strip(b"<>;, ")


def contains_control_chars(s):
    sta(s)  # {u'str/a': 12619, u'uc': 545, u'uc/a': 11496}
    if isinstance(s, six.binary_type):
        s = s.decode('iso-8859-1')
    if CONTROL_CHAR_RE.match(s):
        return True
    return False


def metrics_wrapper():

    def decorate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            return_value = f(*args, **kwargs)
            if 'metrics' in kwargs and kwargs['metrics'] == True:
                #return all values
                return return_value

            # if we have a single item
            if len(return_value[:-1]) == 1:
                return return_value[0]

            # return all except the last value
            return return_value[:-1]

        return wrapper

    return decorate


# allows, \t\n\v\f\r (0x09-0x0d)
CONTROL_CHARS = u''.join(map(six.unichr, list(range(0, 9)) + list(range(14, 32)) + list(range(127, 160))))
CONTROL_CHAR_RE = re.compile(u'[%s]' % re.escape(CONTROL_CHARS), re.UNICODE)


