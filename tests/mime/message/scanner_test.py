# coding:utf-8
from __future__ import absolute_import
from __future__ import print_function
from nose.tools import *
from mock import *
from flanker.mime.message.scanner import scan, ContentType, Boundary
from flanker.mime.message.errors import DecodingError
from email import message_from_string

from ... import *
import six
from six.moves import zip

C = ContentType
B = Boundary

def simple_scan_test():
    message = scan(SIMPLE_2PART)
    eq_('out of inner, in mixed', message.parts[0].body)
    eq_('<p>out of inner, in mixed</p>', message.parts[1].body)


def no_ctype_headers_and_and_boundaries_test():
    """We are ok, when there is no content type and boundaries"""
    message = scan(NO_CTYPE)
    eq_(C(u'text', u'plain', dict(charset=u'ascii')), message.content_type)
    pmessage = message_from_string(NO_CTYPE.decode('utf-8'))
    eq_(message.body, pmessage.get_payload(decode=True).decode('utf-8'))
    for a, b in zip(NO_CTYPE_HEADERS, six.iteritems(message.headers)):
        eq_(a, b)


def multipart_message_test():
    message = scan(EIGHT_BIT)
    pmessage = message_from_string(EIGHT_BIT.decode('utf-8'))

    eq_(C(u'multipart', u'alternative', dict(boundary=u'=-omjqkVTVbwdgCWFRgIkx')),
        message.content_type)

    p = pmessage.get_payload()[0].get_payload(decode=True)
    eq_(p, message.parts[0].body)

    p = pmessage.get_payload()[1].get_payload(decode=True)
    eq_(p, message.parts[1].body)


def enclosed_message_test():
    message = scan(ENCLOSED)
    pmessage = message_from_string(ENCLOSED.decode('utf-8'))

    eq_(C(u'multipart', u'mixed',
          dict(boundary=u'===============6195527458677812340==')),
        message.content_type)
    eq_(u'"Александр Клижентас☯" <bob@example.com>',
        message.headers[b'To'])

    eq_(pmessage.get_payload()[0].get_payload(), message.parts[0].body)

    enclosed = message.parts[1]
    penclosed = pmessage.get_payload(1)

    eq_((u'message/rfc822', {u'name': u'thanks.eml'},),
        enclosed.headers[b'Content-Type'])

    pbody = penclosed.get_payload()[0].get_payload()[0].get_payload(decode=True)
    pbody = six.text_type(pbody, u'utf-8')
    body = enclosed.enclosed.parts[0].body
    eq_(pbody, body)

    body = enclosed.enclosed.parts[1].body
    pbody = penclosed.get_payload()[0].get_payload()[1].get_payload(decode=True)
    pbody = six.text_type(pbody, u'utf-8')
    eq_(pbody, body)


def torture_message_test():
    message = scan(TORTURE)
    tree = tree_to_string(message).splitlines()
    expected = TORTURE_PARTS.splitlines()
    eq_(len(tree), len(expected))
    for a, b in zip(expected, tree):
        eq_(a, b)


def fbl_test():
    message = scan(AOL_FBL)
    eq_(3, len(message.parts))


def ndn_test():
    message = scan(NDN)
    ok_(message.is_delivery_notification())
    eq_(3, len(message.parts))
    eq_('Returned mail: Cannot send message for 5 days',
        message.headers[b'Subject'])
    eq_(u'text/plain', message.parts[0].content_type)
    ok_(message.parts[1].content_type.is_delivery_status())
    ok_(message.parts[2].content_type.is_message_container())
    eq_(u'Hello, how are you',
        message.parts[2].enclosed.headers[b'Subject'])


def ndn_2_test():
    message = scan(BOUNCE)
    ok_(message.is_delivery_notification())
    eq_(3, len(message.parts))
    eq_(u'text/plain', message.parts[0].content_type)
    ok_(message.parts[1].content_type.is_delivery_status())
    ok_(message.parts[2].content_type.is_message_container())


def mailbox_full_test():
    message = scan(MAILBOX_FULL)
    ok_(message.is_delivery_notification())
    eq_(3, len(message.parts))
    eq_(u'text/plain', message.parts[0].content_type)
    ok_(message.parts[1].content_type.is_delivery_status())
    ok_(message.parts[2].content_type.is_headers_container())


def test_uservoice_case():
    message = scan(LONG_LINKS)
    html = message.body
    message._container._body_changed = True
    val = message.to_string()
    for line in val.splitlines():
        print(line)
        ok_(len(line) < 200)
    message = scan(val)
    eq_(html, message.body)


def test_mangle_case():
    m = scan(b"From: a@b.com\r\nTo:b@a.com\n\nFrom here")
    m.body = m.body + u"\nFrom there"
    m = scan(m.to_string())
    eq_(u'From here\nFrom there', m.body)


def test_non_ascii_content_type():
    data = u"""From: me@domain.com
To: you@domain.com
Content-Type: text/点击链接绑定邮箱; charset="us-ascii"

Body.""".encode('utf-8')
    message = scan(data)
    assert_raises(DecodingError, lambda x: message.headers, 1)


def test_non_ascii_from():
    message = scan(FROM_ENCODING)
    eq_(u'"Ingo Lütkebohle" <ingo@blank.pages.de>', message.headers.get(b'from'))


def notification_about_multipart_test():
    message = scan(NOTIFICATION)
    eq_(3, len(message.parts))
    eq_(u'multipart/alternative', message.parts[2].enclosed.content_type)


def dashed_boundaries_test():
    message = scan(DASHED_BOUNDARIES)
    eq_(2, len(message.parts))
    eq_(u'multipart/alternative', message.content_type)
    eq_(u'text/plain', message.parts[0].content_type)
    eq_(u'text/html', message.parts[1].content_type)


def bad_messages_test():
    assert_raises(DecodingError, scan, ENCLOSED_ENDLESS)
    assert_raises(DecodingError, scan, NDN_BROKEN)

def apache_mime_message_news_test():
    message = scan(APACHE_MIME_MESSAGE_NEWS)
    eq_(u'[Fwd: Netscape Enterprise vs. Apache Secure]',
        message.subject)


def missing_final_boundaries_enclosed_test():
    message = scan(ENCLOSED_BROKEN_BOUNDARY)
    eq_((u'message/rfc822', {u'name': u'thanks.eml'},),
        message.parts[1].headers[b'Content-Type'])


def missing_final_boundary_test():
    message = scan(MISSING_FINAL_BOUNDARY)
    ok_(message.parts[0].body)


def weird_bounce_test():
    message = scan(WEIRD_BOUNCE)
    eq_(0, len(message.parts))
    eq_(u'text/plain', message.content_type)

    message = scan(WEIRD_BOUNCE_2)
    eq_(0, len(message.parts))
    eq_(u'text/plain', message.content_type)

    message = scan(WEIRD_BOUNCE_3)
    eq_(0, len(message.parts))
    eq_(u'text/plain', message.content_type)


def bounce_headers_only_test():
    message = scan(NOTIFICATION)
    eq_(3, len(message.parts))
    eq_(u'multipart/alternative',
        str(message.parts[2].enclosed.content_type))

def message_external_body_test():
    message = scan(MESSAGE_EXTERNAL_BODY)
    eq_(2, len(message.parts))
    eq_(message.parts[1].parts[1].content_type.params[u'access-type'], u'anon-ftp')


def messy_content_types_test():
    message = scan(MISSING_BOUNDARIES)
    eq_(0, len(message.parts))


def disposition_notification_test():
    message = scan(DISPOSITION_NOTIFICATION)
    eq_(3, len(message.parts))


def yahoo_fbl_test():
    message = scan(YAHOO_FBL)
    eq_(3, len(message.parts))
    eq_(u'text/html', message.parts[2].enclosed.content_type)


def broken_content_type_test():
    message = scan(SPAM_BROKEN_CTYPE)
    eq_(2, len(message.parts))


def missing_newline_test():
    mime = b"From: Foo <foo@example.com>\r\nTo: Bar <bar@example.com>\r\nMIME-Version: 1.0\r\nContent-type: text/html\r\nSubject: API Message\r\nhello, world\r\n.\r\n"
    message = scan(mime)
    eq_(u"hello, world\r\n.\r\n", message.body)

    # check that works with mixed-style-newlines
    mime = b"From: Foo <foo@example.com>\r\nTo: Bar <bar@example.com>\r\nMIME-Version: 1.0\r\nContent-type: text/html\r\nSubject: API Message\nhello, world"
    message = scan(mime)
    eq_(u"hello, world", message.body)


def tree_to_string(part):
    parts = []
    print_tree(part, parts, u"")
    return u"\n".join(parts)


def print_tree(part, parts, delimiters=""):
    parts.append(u"{0}{1}".format(delimiters, part.content_type))

    if part.content_type.is_multipart():
        for p in part.parts:
            print_tree(p, parts, delimiters + u"-")

    elif part.content_type.is_message_container():
        print_tree(part.enclosed, parts, delimiters + u"-")




NO_CTYPE_HEADERS=[
    (b'Mime-Version', u'1.0'),
    (b'Received', u'by 10.68.60.193 with HTTP; Thu, 29 Dec 2011 02:06:53 -0800 (PST)'),
    (b'X-Originating-Ip', u'[95.37.185.143]'),
    (b'Date', u'Thu, 29 Dec 2011 14:06:53 +0400'),
    (b'Delivered-To', u'bob@marley.com'),
    (b'Message-Id', u'<CAEAsyCbSF1Bk7CBuu6zp3Qs8=j2iUkNi3dPkGe6z40q4dmaogQ@mail.gmail.com>'),
    (b'Subject', u'Testing message parsing'),
    (b'From', u'Bob Marley <bob@marley.com>'),
    (b'To', u'hello@there.com')]


TORTURE_PARTS = u"""multipart/mixed
-text/plain
-message/rfc822
--multipart/alternative
---text/plain
---multipart/mixed
----text/richtext
---application/andrew-inset
-message/rfc822
--audio/basic
-audio/basic
-image/pbm
-message/rfc822
--multipart/mixed
---multipart/mixed
----text/plain
----audio/x-sun
---multipart/mixed
----image/gif
----image/gif
----application/x-be2
----application/atomicmail
---audio/x-sun
-message/rfc822
--multipart/mixed
---text/plain
---image/pgm
---text/plain
-message/rfc822
--multipart/mixed
---text/plain
---image/pbm
-message/rfc822
--application/postscript
-image/gif
-message/rfc822
--multipart/mixed
---audio/basic
---audio/basic
-message/rfc822
--multipart/mixed
---application/postscript
---application/octet-stream
---message/rfc822
----multipart/mixed
-----text/plain
-----multipart/parallel
------image/gif
------audio/basic
-----application/atomicmail
-----message/rfc822
------audio/x-sun
"""
