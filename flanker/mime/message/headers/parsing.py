from __future__ import absolute_import
import string
import regex
from collections import deque
from flanker.mime.message.headers import encodedword, parametrized
from flanker.mime.message.headers.wrappers import ContentType, WithParams
from flanker.mime.message.errors import DecodingError
from flanker.str_analysis import sta
from flanker.utils import to_unicode, is_pure_ascii

MAX_LINE_LENGTH = 10000


def normalize(header):
    sta(header)  # {u'str/a': 7983}
    return string.capwords(header.lower().decode('iso-8859-1'), '-').encode('iso-8859-1')


def parse_stream(stream):
    """Reads the incoming stream and returns list of tuples"""
    out = deque()
    for header in unfold(split(stream)):
        out.append(parse_header(header))
    return out


def parse_header(header):
    """ Accepts a raw header with name, colons and newlines
    and returns it's parsed value
    """
    name, val = split2(header)
    if not is_pure_ascii(name):
        raise DecodingError("Non-ascii header name")
    return name, parse_header_value(name, encodedword.unfold(val))


def parse_header_value(name, val):
    if not is_pure_ascii(val):
        if parametrized.is_parametrized(name, val):
            raise DecodingError("Unsupported value in content- header")
        return to_unicode(val)
    else:
        if parametrized.is_parametrized(name, val):
            val, params = parametrized.decode(val)
            if name == b'Content-Type':
                main, sub = parametrized.fix_content_type(val)
                return ContentType(main, sub, params)
            else:
                return WithParams(val, params)
        else:
            return val


def is_empty(line):
    sta(line)  # {u'str': 7, u'str/a': 5546}
    return line in (b'\r\n', b'\r', b'\n')


RE_HEADER = regex.compile(b'^(From |[\041-\071\073-\176]+:|[\t ])')


def split(fp):
    """Read lines with headers until the start of body"""
    sta(fp)  # {u"<type 'cStringIO.StringI'>": 192}
    lines = deque()
    for line in fp:
        sta(line)  # {u'str': 7, u'str/a': 5156}
        if len(line) > MAX_LINE_LENGTH:
            raise DecodingError(
                "Line is too long: {0}".format(len(line)))

        if is_empty(line):
            break

        # tricky case if it's not a header and not an empty line
        # ususally means that user forgot to separate the body and newlines
        # so "unread" this line here, what means to treat it like a body
        if not RE_HEADER.match(line):
            fp.seek(fp.tell() - len(line))
            break

        lines.append(line)

    return lines


def unfold(lines):
    sta(lines)  # {u'deque()': 12, u'deque(str)': 1, u'deque(str/a)': 174, u'deque(str/a, str)': 4}
    headers = deque()

    for line in lines:
        sta(line)  # {u'str': 6, u'str/a': 4973}
        # ignore unix from
        if line.startswith(b"From "):
            continue
        # this is continuation
        elif line[0] in b' \t':
            extend(headers, line)
        else:
            headers.append(line)

    new_headers = deque()
    for h in headers:
        if isinstance(h, deque):
            sta(h)  # {u'deque(str/a)': 239}
            new_headers.append(b"".join(h).rstrip(b"\r\n"))
        else:
            sta(h)  # {u'str': 6, u'str/a': 974}
            new_headers.append(h.rstrip(b"\r\n"))

    return new_headers


def extend(headers, line):
    sta(headers)  # {u'deque()': 14, u'deque(deque(str/a))': 9, u'deque(deque(str/a), str/a)': 3667, u'deque(str/a)': 59}
    sta(line)  # {u'str/a': 3749}
    try:
        header = headers.pop()
    except IndexError:
        # this means that we got invalid header
        # ignore it
        return

    if isinstance(header, deque):
        header.append(line)
        headers.append(header)
    else:
        headers.append(deque((header, line)))


def split2(header):
    sta(header)  # {u'str': 5, u'str/a': 3866}
    pair = header.split(b":", 1)
    if len(pair) == 2:
        return normalize(pair[0].rstrip()), pair[1].lstrip()
    else:
        return (None, None)
