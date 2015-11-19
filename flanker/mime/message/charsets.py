from __future__ import absolute_import
import regex as re
from flanker.mime.message import errors
from flanker.utils import to_utf8, to_unicode
from flanker.str_analysis import sta


def convert_to_unicode(charset, value):
    # sta(value)  # OK {u'str': 175, u'str/a': 467, u'uc': 76, u'uc/a': 199}
    #in case of unicode we have nothing to do
    if isinstance(value, unicode):
        return value

    charset = _translate_charset(charset)

    return to_unicode(value, charset=charset)


def _translate_charset(charset):
    """Translates crappy charset into Python analogue (if supported).

    Otherwise returns unmodified.
    """
    # ev: (ticket #2819)
    if "sjis" in charset.lower():
        return 'shift_jis'

    # cp874 looks to be an alias for windows-874
    if "windows-874" == charset.lower():
        return "cp874"

    if 'koi8-r' in charset.lower():
        return 'koi8_r'

    if 'utf-8' in charset.lower() or charset.lower() == 'x-unknown':
        return 'utf-8'

    return charset
