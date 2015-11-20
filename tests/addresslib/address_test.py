from __future__ import absolute_import
# coding:utf-8

from .. import *
from nose.tools import assert_equal, assert_not_equal

from flanker.addresslib.address import parse, parse_list
from flanker.addresslib.address import Address, AddressList, EmailAddress, UrlAddress


def test_addr_properties():
    email = parse(b'name@host.com')
    url = parse(b'http://host.com')
    non_ascii = parse(u'Gonzalo Bañuelos<gonz@host.com>')

    eq_(False, url.supports_routing)
    eq_(True,  email.supports_routing)

    eq_(Address.Type.Email, email.addr_type)
    eq_(Address.Type.Url, url.addr_type)
    eq_(non_ascii, b"gonz@host.com")

    adr = parse(b"Zeka <EV@host.coM>")
    eq_(str(adr), 'EV@host.com')


def test_address_compare():
    a = EmailAddress(b"a@host.com")
    b = EmailAddress(b"b@host.com")
    also_a = EmailAddress(b"A@host.com")

    ok_(a == also_a)
    #eq_(False, a != "I am also A <a@HOST.com>")
    ok_(a != b'crap')
    ok_(a != None)
    ok_(a != b)

    u = UrlAddress(b"http://hello.com")
    ok_(u == b"http://hello.com")

    # make sure it works for sets:
    s = set()
    s.add(a)
    s.add(also_a)
    eq_(1, len(s))
    s.add(u)
    s.add(u)
    eq_(2, len(s))

    # test string comparison
    ok_(a == a.address)
    ok_(not (a != a.address))

    ok_(b != a.address)
    ok_(not (b == a.address))


def test_local_url():
    u = UrlAddress(b'http:///foo/bar')
    eq_(None, u.hostname)


def test_addresslist_basics():
    lst = parse_list(b"http://foo.com:1000; Biz@Kontsevoy.Com   ")
    eq_(2, len(lst))
    eq_(b"http", lst[0].scheme)
    eq_(b"kontsevoy.com", lst[1].hostname)
    eq_(b"Biz", lst[1].mailbox)
    ok_(b"biz@kontsevoy.com" in lst)

    # test case-sensitivity: hostname must be lowercased, but the local-part needs
    # to remain case-sensitive
    ok_(b"Biz@kontsevoy.com" in lst)

    # check parsing:
    spec = b'''http://foo.com:8080, "Ev K." <ev@host.com>, "Alex K" alex@yahoo.net; "Tom, S" "tom+[a]"@s.com'''
    lst = parse_list(spec, True)

    eq_(len(lst), 4)
    eq_(b"http://foo.com:8080", lst[0].address)
    eq_(b"ev@host.com", lst[1].address)
    eq_(b"alex@yahoo.net", lst[2].address)
    eq_(b'"tom+[a]"@s.com', lst[3].address)

    # string-based persistence:
    s = str(lst)
    clone = parse_list(s)
    eq_(lst, clone)

    # now clone using full spec:
    s = lst.full_spec()
    clone = parse_list(s)
    eq_(lst, clone)

    # hostnames:
    eq_(set([b'host.com', b'foo.com', b'yahoo.net', b's.com']), lst.hostnames)
    eq_(set(['url', 'email']), lst.addr_types)

    # add:
    result = lst + parse_list(b"ev@local.net") + [b"foo@bar.com"]
    ok_(isinstance(result, AddressList))
    eq_(len(result), len(lst)+2)
    ok_(b"foo@bar.com" in result)


def test_addresslist_with_apostrophe():
    s = b'''"Allan G\'o"  <allan@example.com>, "Os Wi" <oswi@example.com>'''
    lst = parse_list(s)
    eq_(2, len(lst))
    eq_(b'Allan G\'o <allan@example.com>', lst[0].full_spec())
    eq_(b'Os Wi <oswi@example.com>', lst[1].full_spec())
    lst = parse_list(b"=?UTF-8?Q?Eugueny_=CF=8E_Kontsevoy?= <eugueny@gmail.com>")
    eq_(b'=?utf-8?q?Eugueny_=CF=8E_Kontsevoy?= <eugueny@gmail.com>', lst.full_spec())
    eq_(u'Eugueny ώ Kontsevoy', lst[0].display_name)


def test_addresslist_non_ascii_list_input():
    al = [u'Aurélien Berger  <ab@example.com>', b'Os Wi <oswi@example.com>']
    lst = parse_list(al)
    eq_(2, len(lst))
    eq_(b'=?utf-8?q?Aur=C3=A9lien_Berger?= <ab@example.com>', lst[0].full_spec())
    eq_(b'Os Wi <oswi@example.com>', lst[1].full_spec())


def test_addresslist_address_obj_list_input():
    skip_if_asked()  # Bad direct EmailAddress creation, spec is not valid
    al = [EmailAddress(u'Aurélien Berger  <ab@example.com>'),
          UrlAddress(b'https://www.example.com')]
    lst = parse_list(al)
    eq_(2, len(lst))
    eq_(b'=?utf-8?q?Aur=C3=A9lien_Berger?= <ab@example.com>',
        lst[0].full_spec())
    eq_(b'https://www.example.com', lst[1].full_spec())


def test_edge_cases():
    email = EmailAddress(b'"foo.bar@"@example.com')
    eq_(b'"foo.bar@"@example.com', email.address)


def test_display_name__to_full_spec():
    eq_(b'"foo (\\"bar\\") blah" <foo@bar.com>',
        EmailAddress(b'foo ("bar") blah', b'foo@bar.com').full_spec())
    eq_(b'"foo. bar" <foo@bar.com>',
        EmailAddress(b'foo. bar', b'foo@bar.com').full_spec())
    eq_(b'"\\"\\"" <foo@bar.com>',
        EmailAddress(b'""', b'foo@bar.com').full_spec()),
    eq_(b'=?utf-8?b?0J/RgNC40LLQtdGCINCc0LXQtNCy0LXQtA==?= <foo@bar.com>',
        EmailAddress(u'Привет Медвед', 'foo@bar.com').full_spec())


def test_display_name__update():
    # Given
    a = EmailAddress(b'foo bar', b'foo@bar.com')
    eq_(b'foo bar <foo@bar.com>', a.full_spec())

    # When
    a.display_name = u'Привет Медвед'

    # Then
    eq_(b'=?utf-8?b?0J/RgNC40LLQtdGCINCc0LXQtNCy0LXQtA==?= <foo@bar.com>',
        a.full_spec())
