from __future__ import absolute_import
import regex as re
from collections import deque
from io import BytesIO
import sys

from flanker import RE_ASCII_FLAG
from flanker.mime.message.headers import parsing, is_empty, ContentType
from flanker.mime.message.part import MimePart, Stream
from flanker.mime.message.errors import DecodingError
from logging import getLogger
import six

from flanker.str_analysis import sta

log = getLogger(__name__)


def scan(string):
    """Scanner that uses 1 pass to scan the entire message and
    build a message tree"""
    sta(string)  # {u"<type 'type'>": 1, u'list()': 1, u'none': 1, u'str': 9, u'str/a': 116}
    if not isinstance(string, six.binary_type):
        raise DecodingError("Scanner works with byte strings only")

    tokens = tokenize(string)
    if not tokens:
        tokens = [default_content_type()]
    try:
        return traverse(Start(), TokensIterator(tokens, string))
    except DecodingError:
        raise
    except Exception:
        six.reraise(DecodingError("Malformed MIME message"), None, sys.exc_info()[2])


def traverse(pointer, iterator, parent=None):
    """Recursive-descendant parser"""

    iterator.check()
    token = next(iterator)
    sta(token)  # {u"(str/a, <type 'dict'>)": 1048, u"<class 'flanker.mime.message.scanner.Boundary'>": 54}
    # this means that this part does not have any
    # content type set, so set it to RFC default (text/plain)
    # it even can have no headers
    if token.is_end() or token.is_boundary():

        return make_part(
            content_type=default_content_type(),
            start=pointer,
            end=token,
            iterator=iterator,
            parent=parent)

    # this part tells us that it is singlepart
    # so we should ignore all other content-type headers
    # until the boundary or the end of message
    if token.is_singlepart():

        while True:
            iterator.check()
            end = next(iterator)
            if not end.is_content_type():
                break

        return make_part(
            content_type=token,
            start=pointer,
            end=end,
            iterator=iterator,
            parent=parent)

    # good old multipart message
    # here goes the real recursion
    # we scan part by part until the end
    elif token.is_multipart():
        content_type = token

        # well, multipart message should provide
        # some boundary, how could we parse it otherwise?
        boundary = content_type.get_boundary()
        if not boundary:
            raise DecodingError(
                "Multipart message without boundary")

        parts = deque()
        token = next(iterator)

        # we are expecting first boundary for multipart message
        # something is broken otherwise
        if not token.is_boundary() or token != boundary:
            raise DecodingError(
                "Multipart message without starting boundary")

        while True:
            token = iterator.current()
            if token.is_end():
                break
            if isinstance(token, Boundary) and token == boundary and token.is_final():
                next(iterator)
                break
            parts.append(traverse(token, iterator, content_type))

        return make_part(
            content_type=content_type,
            start=pointer,
            end=token,
            iterator=iterator,
            parts=parts,
            parent=parent)

    # this is a weird mime part, actually
    # it can contain multiple headers
    # separated by newlines, so we grab them here
    elif token.is_delivery_status():

        if parent and parent.is_multipart():
            while True:
                iterator.check()
                end = next(iterator)
                if not end.is_content_type():
                    break
        else:
            raise DecodingError("Malformed delivery status message")

        return make_part(
            content_type=token,
            start=pointer,
            end=end,
            iterator=iterator,
            parent=parent)

    # this is a message container that holds
    # a message inside, delimited from parent
    # headers by newline
    elif token.is_message_container():
        enclosed = traverse(pointer, iterator, token)
        return make_part(
            content_type=token,
            start=pointer,
            end=iterator.current(),
            iterator=iterator,
            enclosed=enclosed,
            parent=parent)

    # this part contains headers separated by newlines,
    # grab these headers and enclose them in one part
    elif token.is_headers_container():
        enclosed = grab_headers(pointer, iterator, token)
        return make_part(
            content_type=token,
            start=pointer,
            end=iterator.current(),
            iterator=iterator,
            enclosed=enclosed,
            parent=parent)


def grab_headers(pointer, iterator, parent):
    """This function collects all tokens till the boundary
    or the end of the message. Used to scan parts of the message
    that contain random headers, e.g. text/rfc822-headers"""

    content_type = None
    while True:

        iterator.check()
        end = next(iterator)

        # remember the first content-type we have met when grabbing
        # the headers until the boundary or message end
        if not content_type and end.is_content_type():
            content_type = end

        if not end.is_content_type():
            break

    return make_part(
        content_type=content_type or ContentType(u"text", u"plain"),
        start=pointer,
        end=end,
        iterator=iterator,
        parent=parent)


def default_content_type():
    return ContentType(u"text", u"plain", {u'charset': u'ascii'})


def make_part(content_type, start, end, iterator, parts=[], enclosed=None,
              parent=None):

    # here we detect where the message really starts
    # the exact position in the string, at the end of the
    # starting boundary and after the beginning of the end boundary
    if start.is_boundary():
        start = start.end + 1
    else:
        start = start.start

    # if this is the message ending, end of part
    # the position of the last symbol of the message
    if end.is_end():
        end = len(iterator.string) - 1
    # for multipart boundaries
    # consider the final boundary as the ending one
    elif content_type.is_multipart():
        end = end.end
    # otherwise, end is position of the the symbol before
    # the boundary start
    else:
        end = end.start - 1

    # our tokenizer detected the beginning of the message container
    # that is separated from the enclosed message by newlines
    # here we find where the enclosed message begins by searching for the
    # first newline
    if parent and (parent.is_message_container() or parent.is_headers_container()):
        start = locate_first_newline(iterator.stream, start)

    # ok, finally, create the MimePart.
    # note that it does not parse anything, just remembers
    # the position in the string
    return MimePart(
        container=Stream(
            content_type=content_type,
            start=start,
            end=end,
            stream=iterator.stream,
            string=iterator.string),
        parts=parts,
        enclosed=enclosed,
        is_root=(parent==None))


def locate_first_newline(stream, start):
    """We need to locate the first newline"""
    stream.seek(start)
    for line in stream:
        if is_empty(line):
            return stream.tell()


class TokensIterator(object):

    def __init__(self, tokens, string):
        sta(tokens)  # {u"list((str/a, <type 'dict'>))": 39, u"list(<class 'flanker.mime.message.scanner.Boundary'>, (str/a, <type 'dict'>))": 86}
        sta(string)  # {u'str': 9, u'str/a': 116}
        self.position = -1
        self.tokens = tokens
        self.string = string
        self.stream = BytesIO(string)
        self.opcount = 0

    def next(self):
        self.position += 1
        if self.position >= len(self.tokens):
            return _END
        return self.tokens[self.position]

    def __next__(self):
        return self.next()

    def current(self):
        if self.position >= len(self.tokens):
            return _END
        return self.tokens[self.position]

    def back(self):
        self.position -= 1

    def check(self):
        """ This function is used to protect our lovely scanner
        from the deadloops, we count the number of operations performed
        and will raise an exception if things go wrong (too much ops)
        """
        self.opcount += 1
        if self.opcount > _MAX_OPS:
            raise DecodingError(
                "Too many parts: {0}, max is {1}".format(
                    self.opcount, _MAX_OPS))


@six.python_2_unicode_compatible
class Boundary(object):
    def __init__(self, value, start, end, final=None):
        self.value = value.decode('utf-8')
        self.start = start
        self.end = end
        self.final = final

    def is_final(self):
        return self.final

    def __str__(self):
        return u"Boundary({}, final={})".format(self.value, self.final)

    def __repr__(self):
        return (u"Boundary('{}', {}, {}, final={})"
                .format(self.value, self.start, self.end, self.final))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if isinstance(other, Boundary):
            return self.value == other.value and self.final == other.final
        else:
            if isinstance(other, six.binary_type):
                return self.value == other.decode('iso-8859-1')
            elif isinstance(other, six.text_type):
                return self.value == other
            else:
                return self.value == str(other)

    def is_content_type(self):
        return False

    def is_boundary(self):
        return True

    def is_end(self):
        return False


class End(object):
    def is_end(self):
        return True

    @property
    def start(self):
        return -1

    @property
    def end(self):
        return -1

    def is_boundary(self):
        return False

    def is_content_type(self):
        return False


class Start(object):
    def is_end(self):
        return False

    @property
    def start(self):
        return 0

    @property
    def end(self):
        return 0

    def is_boundary(self):
        return False


_RE_TOKENIZER = re.compile(
    br"""
    (?P<ctype>
        # Note that a content type match corresponds to a Content-Type header
        # only when it is located between a boundary and an empty line.
        ^content-type:

        # The field value consists of printable US-ASCII chars, spaces and tabs.
        [\x21-\x7e\ \t]+

        # The optional field folded part starts from a newline followed by one
        # or more spaces and field value symbols (can not be empty).
        (?:(?:\r\n|\n)[ \t]+[\x20-\x7e \t]+)*
    )
    |
    (?P<boundary>
        # This may be a boundary and may be not we just pre-scan it for future
        # consideration.
        ^--.*
    )
    |
    (?P<empty>
        # This may be a separator that divides message/part headers section
        # and its body.
        ^(\r\n|\n)
    )
    """,
    re.IGNORECASE | re.MULTILINE | re.VERBOSE | RE_ASCII_FLAG)


_CTYPE = 'ctype'
_BOUNDARY = 'boundary'
_END = End()
_MAX_OPS = 500


_SECTION_HEADERS = b'headers'
_SECTION_MULTIPART_PREAMBLE = b'multipart-preamble'
_SECTION_MULTIPART_EPILOGUE = b'multipart-epilogue'
_SECTION_BODY = b'body'

_DEFAULT_CONTENT_TYPE = ContentType(u'text', u'plain', {u'charset': u'us-ascii'})
_EMPTY_LINE = b'\r\n'


def tokenize(string):
    """
    Scans the entire message to find all Content-Types and boundaries.
    """
    sta(string)  # {u'str': 11, u'str/a': 123}
    tokens = deque()
    for m in _RE_TOKENIZER.finditer(string):
        if m.group(_CTYPE):
            name, token = parsing.parse_header(m.group(_CTYPE))
        elif m.group(_BOUNDARY):
            token = Boundary(m.group(_BOUNDARY).strip(b"\t\r\n"),
                             _grab_newline(m.start(), string, -1),
                             _grab_newline(m.end(), string, 1))
        else:
            token = _EMPTY_LINE

        tokens.append(token)
    return _filter_false_tokens(tokens)


def _grab_newline(position, string, direction):
    """
    Boundary can be preceded by `\r\n` or `\n` and can end with `\r\n` or `\n`
    this function scans the line to locate these cases.
    """
    sta(string)  # {u'str': 62, u'str/a': 5320}
    while 0 < position < len(string):
        if string[position:position+1] == b'\n':
            if direction < 0:
                if position - 1 > 0 and string[position-1:position] == b'\r':
                    return position - 1
            return position
        position += direction
    return position


def _filter_false_tokens(tokens):
    """
    Traverses a list of pre-scanned tokens and removes false content-type
    and boundary tokens.

    A content-type header is false unless it it the first content-type header
    in a message/part headers section.

    A boundary token is false if it has not been mentioned in a preceding
    content-type header.
    """
    # sta(tokens) /
    current_section = _SECTION_HEADERS
    current_content_type = None
    filtered = []
    boundaries = []
    for token in tokens:
        sta(token)  # {u"(str/a, <type 'dict'>)": 2653, u"<class 'flanker.mime.message.scanner.Boundary'>": 2691, u'str/a': 6219}
        if isinstance(token, ContentType):
            # Only the first content-type header in a headers section is valid.
            if current_content_type or current_section != _SECTION_HEADERS:
                continue
    
            current_content_type = token
            boundaries.append(token.get_boundary())

        elif isinstance(token, Boundary):
            value = token.value[2:]

            if value in boundaries:
                token.value = value
                token.final = False
                current_section = _SECTION_HEADERS
                current_content_type = None

            elif _strip_endings(value) in boundaries:
                token.value = _strip_endings(value)
                token.final = True
                current_section = _SECTION_MULTIPART_EPILOGUE

            else:
                # False boundary detected!
                continue

        elif token == _EMPTY_LINE:
            if current_section == _SECTION_HEADERS:
                if not current_content_type:
                    current_content_type = _DEFAULT_CONTENT_TYPE

                if current_content_type.is_singlepart():
                    current_section = _SECTION_BODY
                elif current_content_type.is_multipart():
                    current_section = _SECTION_MULTIPART_PREAMBLE
                else:
                    # Start of an enclosed message or just its headers.
                    current_section = _SECTION_HEADERS
                    current_content_type = None

            # Cast away empty line tokens, for they have been pre-scanned just
            # to identify a place where a header section completes and a body
            # section starts.
            continue
        
        else:
            raise DecodingError("Unknown token")

        filtered.append(token)

    return filtered


def _strip_endings(value):
    sta(value)  # {u'str/a': 490}
    if value.endswith(u"--"):
        return value[:-2]
    else:
        return value
