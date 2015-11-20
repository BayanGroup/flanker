from __future__ import absolute_import
# coding:utf-8

from itertools import chain, combinations, permutations

from nose.tools import assert_equal, assert_not_equal
from nose.tools import nottest

from flanker.addresslib import address
from flanker.addresslib.address import EmailAddress, AddressList
from six.moves import range


@nottest
def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

@nottest
def run_relaxed_test(string, expected_mlist, expected_unpar):
    mlist, unpar = address.parse_list(string, strict=False, as_tuple=True)
    assert_equal(mlist, expected_mlist)
    assert_equal(unpar, expected_unpar)

@nottest
def run_strict_test(string, expected_mlist):
    mlist = address.parse_list(string, strict=True)
    assert_equal(mlist, expected_mlist)


BILL_AS = EmailAddress(None, b'bill@microsoft.com')
STEVE_AS = EmailAddress(None, b'steve@apple.com')
LINUS_AS = EmailAddress(None, b'torvalds@kernel.org')

BILL_MBX = EmailAddress(b'Bill Gates', b'bill@microsoft.com')
STEVE_MBX = EmailAddress(b'Steve Jobs', b'steve@apple.com')
LINUS_MBX = EmailAddress(b'Linus Torvalds', b'torvalds@kernel.org')


def test_sanity():
    addr_string = b'Bill Gates <bill@microsoft.com>, Steve Jobs <steve@apple.com>; torvalds@kernel.org'
    run_relaxed_test(addr_string, [BILL_MBX, STEVE_MBX, LINUS_AS], [])
    run_strict_test(addr_string,  [BILL_MBX, STEVE_MBX, LINUS_AS])


def test_simple_valid():
    s = b'''http://foo.com:8080; "Ev K." <ev@host.com>, "Alex K" alex@yahoo.net, "Tom, S" "tom+[a]"@s.com'''
    addrs = address.parse_list(s)

    assert_equal(4, len(addrs))

    assert_equal(addrs[0].addr_type, 'url')
    assert_equal(addrs[0].address, b'http://foo.com:8080')
    assert_equal(addrs[0].full_spec(), b'http://foo.com:8080')

    assert_equal(addrs[1].addr_type, 'email')
    assert_equal(addrs[1].display_name, 'Ev K.')
    assert_equal(addrs[1].address, b'ev@host.com')
    assert_equal(addrs[1].full_spec(), b'"Ev K." <ev@host.com>')

    assert_equal(addrs[2].addr_type, 'email')
    assert_equal(addrs[2].display_name, 'Alex K')
    assert_equal(addrs[2].address, b'alex@yahoo.net')
    assert_equal(addrs[2].full_spec(), b'Alex K <alex@yahoo.net>')

    assert_equal(addrs[3].addr_type, 'email')
    assert_equal(addrs[3].display_name, 'Tom, S')
    assert_equal(addrs[3].address, b'"tom+[a]"@s.com')
    assert_equal(addrs[3].full_spec(), b'"Tom, S" <"tom+[a]"@s.com>')


    s = b'''"Allan G\'o"  <allan@example.com>, "Os Wi" <oswi@example.com>'''
    addrs = address.parse_list(s)

    assert_equal(2, len(addrs))

    assert_equal(addrs[0].addr_type, 'email')
    assert_equal(addrs[0].display_name, 'Allan G\'o')
    assert_equal(addrs[0].address, b'allan@example.com')
    assert_equal(addrs[0].full_spec(), b'Allan G\'o <allan@example.com>')

    assert_equal(addrs[1].addr_type, 'email')
    assert_equal(addrs[1].display_name, 'Os Wi')
    assert_equal(addrs[1].address, b'oswi@example.com')
    assert_equal(addrs[1].full_spec(), b'Os Wi <oswi@example.com>')


    s = u'''I am also A <a@HOST.com>, Zeka <EV@host.coM> ;Gonzalo Bañuelos<gonz@host.com>'''
    addrs = address.parse_list(s)

    assert_equal(3, len(addrs))

    assert_equal(addrs[0].addr_type, 'email')
    assert_equal(addrs[0].display_name, u'I am also A')
    assert_equal(addrs[0].address, b'a@host.com')
    assert_equal(addrs[0].full_spec(), b'I am also A <a@host.com>')

    assert_equal(addrs[1].addr_type, 'email')
    assert_equal(addrs[1].display_name, u'Zeka')
    assert_equal(addrs[1].address, b'EV@host.com')
    assert_equal(addrs[1].full_spec(), b'Zeka <EV@host.com>')

    assert_equal(addrs[2].addr_type, 'email')
    assert_equal(addrs[2].display_name, u'Gonzalo Bañuelos')
    assert_equal(addrs[2].address, b'gonz@host.com')
    assert_equal(addrs[2].full_spec(), b'=?utf-8?q?Gonzalo_Ba=C3=B1uelos?= <gonz@host.com>')


    s = b'''"Escaped" "\e\s\c\\a\p\e\d"@sld.com; http://userid:password@example.com:8080, "Dmitry" <my|'`!#_~%$&{}?^+-*@host.com>'''
    addrs = address.parse_list(s)

    assert_equal(3, len(addrs))

    assert_equal(addrs[0].addr_type, 'email')
    assert_equal(addrs[0].display_name, 'Escaped')
    assert_equal(addrs[0].address, b'"\e\s\c\\a\p\e\d"@sld.com')
    assert_equal(addrs[0].full_spec(), b'Escaped <"\e\s\c\\a\p\e\d"@sld.com>')

    assert_equal(addrs[1].addr_type, 'url')
    assert_equal(addrs[1].address, b'http://userid:password@example.com:8080')
    assert_equal(addrs[1].full_spec(), b'http://userid:password@example.com:8080')

    assert_equal(addrs[2].addr_type, 'email')
    assert_equal(addrs[2].display_name, 'Dmitry')
    assert_equal(addrs[2].address, b'my|\'`!#_~%$&{}?^+-*@host.com')
    assert_equal(addrs[2].full_spec(), b'Dmitry <my|\'`!#_~%$&{}?^+-*@host.com>')


    s = b"http://foo.com/blah_blah_(wikipedia)"
    addrs = address.parse_list(s)

    assert_equal(1, len(addrs))

    assert_equal(addrs[0].addr_type, 'url')
    assert_equal(addrs[0].address, b'http://foo.com/blah_blah_(wikipedia)')
    assert_equal(addrs[0].full_spec(), b'http://foo.com/blah_blah_(wikipedia)')


    s = b"Sasha Klizhentas <klizhentas@gmail.com>"
    addrs = address.parse_list(s)

    assert_equal(1, len(addrs))

    assert_equal(addrs[0].addr_type, 'email')
    assert_equal(addrs[0].display_name, 'Sasha Klizhentas')
    assert_equal(addrs[0].address, b'klizhentas@gmail.com')
    assert_equal(addrs[0].full_spec(), b'Sasha Klizhentas <klizhentas@gmail.com>')


    s = b"admin@mailgunhq.com,lift@example.com"
    addrs = address.parse_list(s)

    assert_equal(2, len(addrs))

    assert_equal(addrs[0].addr_type, 'email')
    assert_equal(addrs[0].display_name, '')
    assert_equal(addrs[0].address, b'admin@mailgunhq.com')
    assert_equal(addrs[0].full_spec(), b'admin@mailgunhq.com')

    assert_equal(addrs[1].addr_type, 'email')
    assert_equal(addrs[1].display_name, '')
    assert_equal(addrs[1].address, b'lift@example.com')
    assert_equal(addrs[1].full_spec(), b'lift@example.com')


def test_simple_invalid():
    s = b'''httd://foo.com:8080\r\n; "Ev K." <ev@ host.com>\n "Alex K" alex@ , "Tom, S" "tom+["  a]"@s.com'''
    assert_equal(address.AddressList(), address.parse_list(s))

    s = b""
    assert_equal(address.AddressList(), address.parse_list(s))

    s = b"crap"
    assert_equal(address.AddressList(), address.parse_list(s))


def test_endpoints():
    # expected result: [foo@example.com, baz@example.com]
    presult = address.parse_list(b'foo@example.com, bar, baz@example.com', strict=False, as_tuple=False)
    assert isinstance(presult, AddressList)
    assert_equal(2, len(presult))

    # expected result: ([foo@example.com, baz@example.com], ['bar'])
    presult = address.parse_list(b'foo@example.com, bar, baz@example.com', strict=False, as_tuple=True)
    assert type(presult) is tuple
    assert_equal(2, len(presult[0]))
    assert_equal(1, len(presult[1]))

    # expected result: [foo@example.com]
    presult = address.parse_list(b'foo@example.com, bar, baz@example.com', strict=True, as_tuple=False)
    assert isinstance(presult, AddressList)
    assert_equal(1, len(presult))

    # expected result: ([foo@example.com], [])
    presult = address.parse_list(b'foo@example.com, bar, baz@example.com', strict=True, as_tuple=True)
    assert type(presult) is tuple
    assert_equal(1, len(presult[0]))
    assert_equal(0, len(presult[1]))


def test_delimiters_relaxed():
    # permutations
    for e in permutations([b' ', b' ', b',', b',', b';', b';']):
        addr_string = b'bill@microsoft.com' + b''.join(e) + b'steve@apple.com, torvalds@kernel.org'
        run_relaxed_test(addr_string, [BILL_AS, STEVE_AS, LINUS_AS], [])

    # powerset
    for e in powerset([b' ', b' ', b',', b',', b';', b';']):
        # empty sets will be tested by the synchronize tests
        if b''.join(e).strip() == b'':
            continue

        addr_string = b'bill@microsoft.com' + b''.join(e) + b'steve@apple.com, torvalds@kernel.org'
        run_relaxed_test(addr_string, [BILL_AS, STEVE_AS, LINUS_AS], [])

def test_delimiters_strict():
    # permutations
    for e in permutations([b' ', b' ', b',', b',', b';', b';']):
        addr_string = b'bill@microsoft.com' + b''.join(e) + b'steve@apple.com, torvalds@kernel.org'
        run_strict_test(addr_string, [BILL_AS, STEVE_AS, LINUS_AS])

    # powerset
    for e in powerset([b' ', b' ', b',', b',', b';', b';']):
        # empty sets will be tested by the synchronize tests
        if b''.join(e).strip() == b'':
            continue

        addr_string = b'bill@microsoft.com' + b''.join(e) + b'steve@apple.com, torvalds@kernel.org'
        run_strict_test(addr_string, [BILL_AS, STEVE_AS, LINUS_AS])


def test_synchronize_relaxed():
    run_relaxed_test(b'"@microsoft.com, steve@apple.com', [STEVE_AS], [b'"@microsoft.com'])
    run_relaxed_test(b'"@microsoft.com steve@apple.com', [], [b'"@microsoft.com steve@apple.com'])
    run_relaxed_test(b'"@microsoft.comsteve@apple.com', [], [b'"@microsoft.comsteve@apple.com'])

    run_relaxed_test(b'bill@microsoft.com, steve, torvalds@kernel.org', [BILL_AS, LINUS_AS], [b'steve'])
    run_relaxed_test(b'bill@microsoft.com, steve torvalds', [BILL_AS], [b'steve torvalds'])

    run_relaxed_test(b'bill;  ', [], [b'bill'])
    run_relaxed_test(b'bill ;', [], [b'bill '])
    run_relaxed_test(b'bill ; ', [], [b'bill '])

    run_relaxed_test(b'bill@microsoft.com;  ', [BILL_AS],  [])
    run_relaxed_test(b'bill@microsoft.com ;', [BILL_AS], [])
    run_relaxed_test(b'bill@microsoft.com ; ', [BILL_AS], [] )

    run_relaxed_test(b'bill; steve; linus', [], [b'bill', b'steve', b'linus'])

    run_relaxed_test(b',;@microsoft.com, steve@apple.com', [STEVE_AS], [b'@microsoft.com'])
    run_relaxed_test(b',;"@microsoft.comsteve@apple.com', [], [b'"@microsoft.comsteve@apple.com'])


def test_synchronize_strict():
    run_strict_test(b'"@microsoft.com, steve@apple.com', [])
    run_strict_test(b'"@microsoft.com steve@apple.com', [])
    run_strict_test(b'"@microsoft.comsteve@apple.com', [])

    run_strict_test(b'bill@microsoft.com, steve, torvalds@kernel.org', [BILL_AS])
    run_strict_test(b'bill@microsoft.com, steve torvalds', [BILL_AS])

    run_strict_test(b'bill;  ', [])
    run_strict_test(b'bill ;', [])
    run_strict_test(b'bill ; ', [])

    run_strict_test(b'bill@microsoft.com;  ', [BILL_AS])
    run_strict_test(b'bill@microsoft.com ;', [BILL_AS])
    run_strict_test(b'bill@microsoft.com ; ', [BILL_AS])

    run_strict_test(b'bill; steve; linus', [])

    run_strict_test(b',;@microsoft.com, steve@apple.com', [])
    run_strict_test(b'",;@microsoft.com steve@apple.com', [])
    run_strict_test(b',;"@microsoft.comsteve@apple.com', [])
