from __future__ import absolute_import
import email.message
import flanker.addresslib.address
import logging

from collections import deque
from email.header import Header
from flanker.mime.message.headers import parametrized
from flanker.str_analysis import sta
from flanker.utils import to_utf8
import six

log = logging.getLogger(__name__)

# max length for a header line is 80 chars
# max recursion depth is 1000
# 80 * 1000 for header is too much for the system
# so we allow just 100 lines for header
MAX_HEADER_LENGTH = 8000

ADDRESS_HEADERS = ('From', 'To', 'Delivered-To', 'Cc', 'Bcc', 'Reply-To')


def to_mime(key, value):
    sta(key)  # {u'str/a': 693}
    sta(value)  # {u"(str/a, <type 'dict'>)": 169, u'str/a': 504, u'uc': 13, u'uc/a': 7}
    if not value:
        return ""

    if type(value) == list:
        return "; ".join(encode(key, v) for v in value)
    else:
        return encode(key, value)


def encode(name, value):
    sta(name)  # {u'str/a': 683}
    sta(value)  # {u"(str/a, <type 'dict'>)": 169, u'str/a': 494, u'uc': 13, u'uc/a': 7}
    try:
        if parametrized.is_parametrized(name, value):
            value, params = value
            return encode_parametrized(name, value, params)
        else:
            return encode_unstructured(name, value)
    except Exception:
        log.exception("Failed to encode %s %s" % (name, value))
        raise


def encode_unstructured(name, value):
    sta(name)  # {u'str/a': 518}
    sta(value)  # {u'str/a': 496, u'uc': 15, u'uc/a': 7}
    if len(value) > MAX_HEADER_LENGTH:
        return to_utf8(value)
    try:
        return Header(
            value.encode("ascii"), "ascii",
            header_name=name).encode(splitchars=' ;,')
    except UnicodeEncodeError:
        if is_address_header(name, value):
            return encode_address_header(name, value)
        else:
            return Header(
                to_utf8(value), "utf-8",
                header_name=name).encode(splitchars=' ;,')


def encode_address_header(name, value):
    out = deque()
    for addr in flanker.addresslib.address.parse_list(value):
        out.append(addr.full_spec())
    return "; ".join(out)


def encode_parametrized(key, value, params):
    if params:
        params = [encode_param(key, n, v) for n, v in six.iteritems(params)]
        return value + "; " + ("; ".join(params))
    else:
        return value


def encode_param(key, name, value):
    try:
        value = value.encode("ascii")
        return email.message._formatparam(name, value)
    except Exception:
        value = Header(value.encode("utf-8"), "utf-8",  header_name=key).encode(splitchars=' ;,')
        return email.message._formatparam(name, value)


def encode_string(name, value, maxlinelen=None):
    try:
        header = Header(value.encode("ascii"), "ascii", maxlinelen,
                        header_name=name)
    except UnicodeEncodeError:
        header = Header(value.encode("utf-8"), "utf-8", header_name=name)

    return header.encode(splitchars=' ;,')


def is_address_header(key, val):
    return key in ADDRESS_HEADERS and '@' in val
