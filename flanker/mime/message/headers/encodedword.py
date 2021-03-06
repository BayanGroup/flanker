from __future__ import absolute_import
# coding:utf-8
import logging
import regex as re

import email.quoprimime
import email.base64mime

from base64 import b64encode

from flanker.mime.message import charsets, errors
from flanker.str_analysis import sta
import six

log = logging.getLogger(__name__)

#deal with unfolding
UNICODE_foldingWhiteSpace = re.compile(u"(\n\r?|\r\n?)(\s*)")
BYTES_foldingWhiteSpace = re.compile(b"(\n\r?|\r\n?)(\s*)")


def unfold(value):
    """
    Unfolding is accomplished by simply removing any CRLF
    that is immediately followed by WSP.  Each header field should be
    treated in its unfolded form for further syntactic and semantic
    evaluation.
    """
    sta(value)  # {u'str': 6, u'str/a': 7438, u'uc': 69, u'uc/a': 152}
    if isinstance(value, six.binary_type):
        return re.sub(BYTES_foldingWhiteSpace, br"\2", value)
    else:
        return re.sub(UNICODE_foldingWhiteSpace, u"\\2", value)


def decode(header):
    sta(header)  # {u"(none, <type 'dict'>)": 9, u"(str/a, <type 'dict'>)": 354, u"<type 'int'>": 4, u'str/a': 367, u'uc': 7, u'uc/a': 3}
    return mime_to_unicode(header)


def mime_to_unicode(header):
    """
    Takes a header value and returns a fully decoded unicode string.
    It differs from standard Python's mail.header.decode_header() because:
        - it is higher level, i.e. returns a unicode string instead of
          an array of tuples
        - it accepts Unicode and non-ASCII strings as well

    >>> header_to_unicode("=?UTF-8?B?UmVbMl06INCX0LXQvNC70Y/QutC4?=")
        u"Земляки"
    >>> header_to_unicode("hello")
        u"Hello"
    """
    sta(header)  # {u"(none, <class 'dict'>)": 2, u"(str/a, <class 'dict'>)": 124, u'str/a': 27}
    # Only string header values need to be converted.
    if not isinstance(header, (six.text_type, six.binary_type)):
        return header

    if isinstance(header, six.binary_type):
        header = header.decode('iso-8859-1')
    try:
        header = unfold(header)
        decoded = []  # decoded parts

        while header:
            match = encodedWord.search(header)
            if match:
                start = match.start()
                if start != 0:
                    # decodes unencoded ascii part to unicode
                    value = charsets.convert_to_unicode(ascii, header[0:start])
                    if value.strip():
                        decoded.append(value)
                # decode a header =?...?= of encoding
                charset, value = decode_part(
                    match.group('charset').lower(),
                    match.group('encoding').lower(),
                    match.group('encoded'))
                if isinstance(value, six.text_type):
                    value = value.encode('iso-8859-1')  # walk-around for email.quoprimime.header_decode always returning str
                decoded.append(charsets.convert_to_unicode(charset, value))
                header = header[match.end():]
            else:
                # no match? append the remainder
                # of the string to the list of chunks
                decoded.append(charsets.convert_to_unicode(ascii, header))
                break
        return u"".join(decoded)
    except Exception as e:
        try:
            logged_header = header
            if isinstance(logged_header, six.text_type):
                logged_header = logged_header.encode('utf-8')
                # encode header as utf-8 so all characters can be base64 encoded
            logged_header = b64encode(logged_header)
            log.warning(
                u"HEADER-DECODE-FAIL: ({0}) - b64encoded".format(
                    logged_header))
        except Exception:
            log.exception("Failed to log exception")
        return header


ascii = 'ascii'

#this spec refers to
#http://tools.ietf.org/html/rfc2047
encodedWord = re.compile(u'''(?P<encodedWord>
  =\?                  # literal =?
  (?P<charset>[^?]*?)  # non-greedy up to the next ? is the charset
  \?                   # literal ?
  (?P<encoding>[qb])   # either a "q" or a "b", case insensitive
  \?                   # literal ?
  (?P<encoded>.*?)     # non-greedy up to the next ?= is the encoded string
  \?=                  # literal ?=
)''', re.VERBOSE | re.IGNORECASE | re.MULTILINE)


def decode_part(charset, encoding, value):
    """
    Attempts to decode part, understands
    'q' - quoted encoding
    'b' - base64 mime encoding

    Returns (charset, decoded-string)
    """
    sta(encoding)
    if encoding == 'q':
        return (charset, email.quoprimime.header_decode(str(value)))

    elif encoding == 'b':
        # Postel's law: add missing padding
        paderr = len(value) % 4
        if paderr:
            value += '==='[:4 - paderr]
        return (charset, email.base64mime.decode(value))

    elif not encoding:
        return (charset, value)

    else:
        raise errors.DecodingError(
            "Unknown encoding: {0}".format(encoding))
