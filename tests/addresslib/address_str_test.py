from __future__ import absolute_import
# coding:utf-8

from .. import *
from nose.tools import assert_equal, assert_not_equal

from flanker.addresslib.address import parse, parse_list
from flanker.addresslib.address import Address, AddressList, EmailAddress, UrlAddress


def test_address_list_repr():
    email = parse_list(None)
    eq_(repr(email), '[]')


