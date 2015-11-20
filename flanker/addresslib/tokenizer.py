# coding:utf-8

"""
TokenStream represents a stream of tokens that a parser will consume.
TokenStream can be used to consume tokens, peek ahead, and synchonize to a
delimiter token. The tokens that the token stream operates on are either
compiled regular expressions or strings.
"""
from __future__ import absolute_import

import re
from flanker.addresslib import ASCII_FLAG
import six


LBRACKET   = b'<'
AT_SYMBOL  = b'@'
RBRACKET   = b'>'
DQUOTE     = b'"'

BAD_DOMAIN = re.compile(br'''                                    # start or end
                        ^-|-$                                   # with -
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

DELIMITER  = re.compile(br'''
                        [,;][,;\s]*                             # delimiter
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

WHITESPACE = re.compile(br'''
                        (\ |\t)+                                # whitespace
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

UNI_WHITE  = re.compile(u'''
                        [
                            \u0020\u00a0\u1680\u180e
                            \u2000-\u200a
                            \u2028\u202f\u205f\u3000
                        ]*
                        ''', re.MULTILINE | re.VERBOSE | re.UNICODE)

RELAX_ATOM = re.compile(br'''
                        ([^\s<>;,"]+)
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

ATOM       = re.compile(br'''
                        [A-Za-z0-9!#$%&'*+\-/=?^_`{|}~]+        # atext
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

DOT_ATOM   = re.compile(br'''
                        [A-Za-z0-9!#$%&'*+\-/=?^_`{|}~]+        # atext
                        (\.[A-Za-z0-9!#$%&'*+\-/=?^_`{|}~]+)*   # (dot atext)*
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

UNI_ATOM = re.compile(u'''
                        ([^\s<>;,"]+)
                        ''', re.MULTILINE | re.VERBOSE | re.UNICODE)

UNI_QSTR   = re.compile(u'''
                        "
                        (?P<qstr>([^"]+))
                        "
                        ''', re.MULTILINE | re.VERBOSE | re.UNICODE)

QSTRING    = re.compile(br'''
                        "                                       # dquote
                        (\s*                                    # whitespace
                        ([\x21\x23-\x5b\x5d-\x7e]               # qtext
                        |                                       # or
                        \\[\x21-\x7e\t\ ]))*                    # quoted-pair
                        \s*                                     # whitespace
                        "                                       # dquote
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

URL        = re.compile(br'''
                        (?:http|https)://
                        [^\s<>{}|\^~\[\]`;,]+
                        ''', re.MULTILINE | re.VERBOSE | ASCII_FLAG)

UNI_URL        = re.compile(u'''
                        (?:http|https)://
                        [^\s<>{}|\^~\[\]`;,]+
                        ''', re.MULTILINE | re.VERBOSE | re.UNICODE)

class TokenStream(object):
    """
    Represents the stream of tokens that the parser will consume. The token
    stream can be used to consume tokens, peek ahead, and synchonize to a
    delimiter token.

    When the strem reaches its end, the position is placed
    at one plus the position of the last token.
    """
    def __init__(self, stream):
        self.position = 0
        self.stream = stream
        # sta(self.stream)  # OK {u'str/a': 6781, u'uc': 240, u'uc/a': 1711}

    def get_token(self, token, ngroup=None):
        """
        Get the next token from the stream and advance the stream. Token can
        be either a compiled regex or a string.
        """
        # sta((token, self.stream)) # OK {u'(re/b-, str/a)': 101863, u'(re/b-, uc)': 3369, u'(re/b-, uc/a)': 65700, u'(re/uu, str/a)': 53086, u'(re/uu, uc)': 2305, u'(re/uu, uc/a)': 39106, u'(str/a, str/a)': 15648, u'(str/a, uc)': 436, u'(str/a, uc/a)': 10728}
        # match single character
        if isinstance(token, six.binary_type) and len(token) == 1:
            if isinstance(self.stream, six.text_type):
                token = token.decode('iso-8859-1')
            # sta((token, self.stream)) # OK {u'(str/a, str/a)': 15648, u'(uc/a, uc)': 436, u'(uc/a, uc/a)': 10728}
            if self.peek() == token:
                self.position += 1
                return token
            return None

        if isinstance(token, six.text_type) and len(token) == 1:
            if isinstance(self.stream, six.binary_type):
                token = token.encode('iso-8859-1')
            # sta((token, self.stream)) # OK {}
            if self.peek() == token:
                self.position += 1
                return token
            return None

        # do not match a unicode pattern against bytes stream
        if isinstance(token.pattern, six.text_type) and isinstance(self.stream, six.binary_type):
            # sta((token, self.stream)) # OK {u'(re/uu, str/a)': 53086}
            return None

        # convert bytes pattern to unicode when matching against a unicode stream
        if isinstance(token.pattern, six.binary_type) and isinstance(self.stream, six.text_type):
            token = re.compile(token.pattern.decode('iso-8859-1'), token.flags | ASCII_FLAG)

        # sta((token, self.stream)) # {u'(re/b-, str/a)': 101863, u'(re/u-, uc)': 3369, u'(re/u-, uc/a)': 65700, u'(re/uu, uc)': 2305, u'(re/uu, uc/a)': 39106}
        # match a pattern
        match = token.match(self.stream, self.position)
        if match:
            advance = match.end() - match.start()
            self.position += advance

            # if we are asking for a named capture, return jus that
            if ngroup:
                return match.group(ngroup)
            # otherwise return the entire capture
            return match.group()

        return None

    def end_of_stream(self):
        """
        Check if the end of the stream has been reached, if it has, returns
        True, otherwise false.
        """
        if self.position >= len(self.stream):
            return True
        return False

    def synchronize(self):
        """
        Advances the stream to synchronizes to the delimiter token. Used primarily
        in relaxed mode parsing.
        """
        start_pos = self.position
        end_pos = len(self.stream)

        delimiter = DELIMITER
        # convert bytes pattern to unicode when matching against a unicode stream
        if isinstance(delimiter.pattern, six.binary_type) and isinstance(self.stream, six.text_type):
            delimiter = re.compile(delimiter.pattern.decode('iso-8859-1'), delimiter.flags)

        match = delimiter.search(self.stream, self.position)
        if match:
            self.position = match.start()
            end_pos = match.start()
        else:
            self.position = end_pos

        skip = self.stream[start_pos:end_pos]
        if len(skip.strip()) == 0:
            return None

        return skip

    def peek(self, token=None):
        """
        Peek at the stream to see what the next token is or peek for a
        specific token.
        """
        # sta((token, self.stream)) # OK {u'(none, str/a)': 15648, u'(none, uc)': 436, u'(none, uc/a)': 10728, u'(re/b-, str/a)': 10240, u'(re/b-, uc)': 71, u'(re/b-, uc/a)': 10566, u'(re/uu, str/a)': 18890, u'(re/uu, uc)': 290, u'(re/uu, uc/a)': 15882}
        # peek at whats next in the stream
        if token is None:
            if self.position < len(self.stream):
                return self.stream[self.position:self.position+1]
            else:
                return None
        # peek for a specific token
        else:
            # do not match a unicode pattern against bytes stream
            if isinstance(token.pattern, six.text_type) and isinstance(self.stream, six.binary_type):
                # sta((token, self.stream)) # OK {u'(re/uu, str/a)': 18890}
                return None

            # convert bytes pattern to unicode when matching against a unicode stream
            if isinstance(token.pattern, six.binary_type) and isinstance(self.stream, six.text_type):
                token = re.compile(token.pattern.decode('iso-8859-1'), token.flags)

            # sta((token, self.stream)) # OK {u'(re/b-, str/a)': 10240, u'(re/u-, uc)': 71, u'(re/u-, uc/a)': 10566, u'(re/uu, uc)': 290, u'(re/uu, uc/a)': 15882}
            match = token.match(self.stream, self.position)
            if match:
                return self.stream[match.start():match.end()]
            return None
