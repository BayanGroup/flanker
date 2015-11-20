from __future__ import absolute_import
# coding:utf-8

import re

from .. import *

from nose.tools import assert_equal, assert_not_equal
from flanker.addresslib import address

COMMENT = re.compile(b'''\s*#''')
COMMENT_UNICODE = re.compile(u'''\s*#''')


def test_mailbox_valid_set():
    for line in MAILBOX_VALID_TESTS.split(b'\n'):
        # strip line, skip over empty lines
        line = line.strip()
        if line == b'':
            continue

        # skip over comments or empty lines
        match = COMMENT.match(line)
        if match:
            continue

        mbox = address.parse(line)
        assert_not_equal(mbox, None)

def test_mailbox_invalid_set():
    for line in MAILBOX_INVALID_TESTS.split(b'\n'):
        # strip line, skip over empty lines
        line = line.strip()
        if line == b'':
            continue

        # skip over comments
        match = COMMENT.match(line)
        if match:
            continue

        mbox = address.parse(line)
        assert_equal(mbox, None)

def test_url_valid_set():
    for line in URL_VALID_TESTS.split(u'\n'):
        # strip line, skip over empty lines
        line = line.strip()
        if line == u'':
            continue

        # skip over comments or empty lines
        match = COMMENT_UNICODE.match(line)
        if match:
            continue

        mbox = address.parse(line)
        assert_not_equal(mbox, None)

def test_url_invalid_set():
    for line in URL_INVALID_TESTS.split(u'\n'):
        # strip line, skip over empty lines
        line = line.strip()
        if line == u'':
            continue

        # skip over comments
        match = COMMENT_UNICODE.match(line)
        if match:
            continue

        mbox = address.parse(line)
        assert_equal(mbox, None)
