from __future__ import absolute_import
from io import StringIO, BytesIO
import re
from flanker.addresslib.tokenizer import ATOM, WHITESPACE

from flanker.str_analysis import sta, statype
import six

_RE_ATOM_PHRASE = re.compile(
    b'(' + ATOM.pattern + b'(' + WHITESPACE.pattern + ATOM.pattern + b')*)|^$',
    re.MULTILINE | re.VERBOSE)


def smart_quote(s):
    """
    Quotes the input string but only if it contains at least one word that is
    not an rfc2822 atom. That is probably a little bit excessive but we better
    be safe then sorry.
    """
    # sta(s)  # OK {u'str/a': 131}
    if _contains_atoms_only(s):
        return s

    return b'"' + s.replace(b'\\', b'\\\\').replace(b'"', b'\\"') + b'"'


def smart_unquote(s):
    """
    Returns a string that is created from the input string by unquoting all
    quoted regions in there. If there are no quoted regions in the input string
    then output string is identical to the input string.
    """
    # sta(s)  # OK {u'str/a': 4, u'uc': 109, u'uc/a': 88}
    if isinstance(s, six.text_type):
        quote_char = u'"'
        escape_char = u'\\'
        unquoted = StringIO()
    else:
        quote_char = b'"'
        escape_char = b'\\'
        unquoted = BytesIO()
        s = [s[i:i+1] for i in range(len(s))]
    escaped_char = False
    is_quoted_section = False
    for c in s:
        if is_quoted_section:
            if escaped_char:
                escaped_char = False
            else:
                if c == quote_char:
                    is_quoted_section = False
                    continue
                elif c == escape_char:
                    escaped_char = True
                    continue
        else:
            if c == quote_char:
                is_quoted_section = True
                continue

        unquoted.write(c)

    return unquoted.getvalue()


def _contains_atoms_only(s):
    match_result = _RE_ATOM_PHRASE.match(s)
    return match_result and match_result.end(0) == len(s)
