from __future__ import absolute_import
from io import BytesIO, StringIO
from contextlib import closing
from email.generator import Generator

import six


def python_message_to_string(msg):
    """Converts python message to string in a proper way"""
    if six.PY2:
        with closing(BytesIO()) as fp:
            g = Generator(fp, mangle_from_=False)
            g.flatten(msg, unixfrom=False)
            return fp.getvalue().encode('iso-8859-1')
    else:
        with closing(StringIO()) as fp:
            g = Generator(fp, mangle_from_=False)
            g.flatten(msg, unixfrom=False)
            return fp.getvalue().encode('iso-8859-1')
