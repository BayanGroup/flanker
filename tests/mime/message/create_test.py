# coding:utf-8

from nose.tools import *
from mock import *

import email
import json

from base64 import b64decode

from flanker.mime import create
from flanker.mime.message import errors
from flanker.mime.message.part import MimePart
from email.parser import Parser

from ... import *


def from_python_message_test():
    python_message = Parser().parsestr(MULTIPART.decode('utf-8'))
    message = create.from_python(python_message)

    eq_(python_message['Subject'], message.headers[b'Subject'])

    ctypes = [p.get_content_type() for p in python_message.walk()]
    ctypes2 = [str(p.content_type) for p in message.walk(with_self=True)]
    eq_(ctypes, ctypes2)

    payloads = [p.get_payload(decode=True) for p in python_message.walk()][1:]
    payloads2 = [(p.body.encode('utf-8') if p.body else p.body) for p in message.walk()]

    eq_(payloads, payloads2)


def from_string_message_test():
    message = create.from_string(IPHONE)
    parts = list(message.walk())
    eq_(3, len(parts))
    eq_(u'\n\n\n~Danielle', parts[2].body)


def from_part_message_simple_test():
    message = create.from_string(IPHONE)
    parts = list(message.walk())

    message = create.from_message(parts[2])
    eq_(u'\n\n\n~Danielle', message.body)


def message_from_garbage_test():
    assert_raises(errors.DecodingError, create.from_string, None)
    assert_raises(errors.DecodingError, create.from_string, [])
    assert_raises(errors.DecodingError, create.from_string, MimePart)


def create_singlepart_ascii_test():
    message = create.text(u"plain", u"Hello")
    message = create.from_string(message.to_string())
    eq_(u"7bit", message.content_encoding.value)
    eq_("Hello", message.body)


def create_singlepart_unicode_test():
    message = create.text(u"plain", u"Привет, курилка")
    message = create.from_string(message.to_string())
    eq_(u"base64", message.content_encoding.value)
    eq_(u"Привет, курилка", message.body)


def create_singlepart_ascii_long_lines_test():
    very_long = "very long line  " * 1000 + "preserve my newlines \r\n\r\n"
    message = create.text(u"plain", very_long)

    message2 = create.from_string(message.to_string())
    eq_(u"quoted-printable", message2.content_encoding.value)
    eq_(very_long, message2.body)

    message2 = email.message_from_string(message.to_string().decode('utf-8'))
    eq_(very_long, message2.get_payload(decode=True))


def create_multipart_simple_test():
    message = create.multipart(u"mixed")
    message.append(
        create.text(u"plain", "Hello"),
        create.text(u"html", "<html>Hello</html>"))
    ok_(message.is_root())
    assert_false(message.parts[0].is_root())
    assert_false(message.parts[1].is_root())

    message2 = create.from_string(message.to_string())
    eq_(2, len(message2.parts))
    eq_(u"multipart/mixed", message2.content_type)
    eq_(2, len(message.parts))
    eq_("Hello", message.parts[0].body)
    eq_("<html>Hello</html>", message.parts[1].body)

    message2 = email.message_from_string(message.to_string().decode())
    eq_("multipart/mixed", message2.get_content_type())
    eq_("Hello", message2.get_payload()[0].get_payload(decode=False))
    eq_("<html>Hello</html>",
        message2.get_payload()[1].get_payload(decode=False))


def create_multipart_with_attachment_test():
    message = create.multipart(u"mixed")
    filename = u"Мейлган картиночка картиночечка с длинным  именем и пробельчиками"
    message.append(
        create.text(u"plain", "Hello"),
        create.text(u"html", "<html>Hello</html>"),
        create.binary(
            u"image", u"png", MAILGUN_PNG,
            filename, u"attachment"))
    eq_(3, len(message.parts))

    message2 = create.from_string(message.to_string())
    eq_(3, len(message2.parts))
    eq_(u"base64", message2.parts[2].content_encoding.value)
    eq_(MAILGUN_PNG, message2.parts[2].body)
    eq_(filename, message2.parts[2].content_disposition.params[u'filename'])
    eq_(filename, message2.parts[2].content_type.params[u'name'])
    ok_(message2.parts[2].is_attachment())

    message2 = email.message_from_string(message.to_string().decode('utf-8'))
    eq_(3, len(message2.get_payload()))
    eq_(MAILGUN_PNG, message2.get_payload()[2].get_payload(decode=True))


def create_multipart_with_text_non_unicode_attachment_test():
    """Make sure we encode text attachment in base64
    """
    message = create.multipart(u"mixed")
    filename = u"text-attachment.txt"
    message.append(
        create.text(u"plain", "Hello"),
        create.text(u"html", "<html>Hello</html>"),
        create.binary(
            u"text", u"plain", u"Саша с уралмаша".encode("koi8-r"),
            filename, u"attachment"))

    message2 = create.from_string(message.to_string())

    eq_(3, len(message2.parts))
    attachment = message2.parts[2]
    ok_(attachment.is_attachment())
    eq_(u"base64", attachment.content_encoding.value)
    eq_(u"Саша с уралмаша", attachment.body)


def create_multipart_with_text_non_unicode_attachment_preserve_encoding_test():
    """Make sure we encode text attachment in base64
    and also preserve charset information
    """
    message = create.multipart(u"mixed")
    filename = "text-attachment.txt"
    message.append(
        create.text(u"plain", "Hello"),
        create.text(u"html", "<html>Hello</html>"),
        create.text(
            u"plain",
            u"Саша с уралмаша 2".encode("koi8-r"),
            u"koi8-r",
            u"attachment",
            filename))

    message2 = create.from_string(message.to_string())

    eq_(3, len(message2.parts))
    attachment = message2.parts[2]
    ok_(attachment.is_attachment())
    eq_(u"base64", attachment.content_encoding.value)
    eq_(u"koi8-r", attachment.charset)
    eq_(u"Саша с уралмаша 2", attachment.body)


def create_multipart_nested_test():
    message = create.multipart(u"mixed")
    nested = create.multipart(u"alternative")
    nested.append(
        create.text(u"plain", u"Саша с уралмаша"),
        create.text(u"html", u"<html>Саша с уралмаша</html>"))
    message.append(
        create.text(u"plain", "Hello"),
        nested)

    message2 = create.from_string(message.to_string())
    eq_(2, len(message2.parts))
    eq_(u'text/plain', message2.parts[0].content_type)
    eq_('Hello', message2.parts[0].body)

    eq_(u"Саша с уралмаша", message2.parts[1].parts[0].body)
    eq_(u"<html>Саша с уралмаша</html>", message2.parts[1].parts[1].body)


def create_enclosed_test():
    message = create.text(u"plain", u"Превед")
    message.headers[b'From'] = u' Саша <sasha@mailgun.net>'
    message.headers[b'To'] = u'Женя <ev@mailgun.net>'
    message.headers[b'Subject'] = u"Все ли ок? Нормальненько??"

    message = create.message_container(message)

    message2 = create.from_string(message.to_string())
    eq_(u'message/rfc822', message2.content_type)
    eq_(u"Превед", message2.enclosed.body)
    eq_(u'Саша <sasha@mailgun.net>', message2.enclosed.headers[b'From'])


def create_enclosed_nested_test():
    nested = create.multipart(u"alternative")
    nested.append(
        create.text(u"plain", u"Саша с уралмаша"),
        create.text(u"html", u"<html>Саша с уралмаша</html>"))

    message = create.multipart(u"mailgun-recipient-variables")
    variables = {u"a": u"<b>Саша</b>" * 1024}
    message.append(
        create.binary(u"application", u"json", json.dumps(variables).encode('utf-8')),
        create.message_container(nested))

    message2 = create.from_string(message.to_string())
    eq_(variables, json.loads(message2.parts[0].body.decode('utf-8')))

    nested = message2.parts[1].enclosed
    eq_(2, len(nested.parts))
    eq_(u"Саша с уралмаша", nested.parts[0].body)
    eq_(u"<html>Саша с уралмаша</html>", nested.parts[1].body)


def guessing_attachments_test():
    binary = create.binary(
        u"application", u'octet-stream', MAILGUN_PNG, '/home/alex/mailgun.png')
    eq_(u'image/png', binary.content_type)
    eq_('mailgun.png', binary.content_type.params['name'])

    binary = create.binary(
        u"application", u'octet-stream',
        MAILGUN_PIC, '/home/alex/mailgun.png', disposition=u'attachment')

    eq_(u'attachment', binary.headers[b'Content-Disposition'].value)
    eq_('mailgun.png', binary.headers[b'Content-Disposition'].params['filename'])

    binary = create.binary(
        u"application", u'octet-stream', NOTIFICATION, '/home/alex/mailgun.eml')
    eq_(u'message/rfc822', binary.content_type)

    binary = create.binary(
        u"application", u'octet-stream', MAILGUN_WAV, '/home/alex/audiofile.wav')
    eq_(u'audio/x-wav', binary.content_type)


def attaching_emails_test():
    attachment = create.attachment(
        u"message/rfc822", MULTIPART, "message.eml", u"attachment")
    eq_(u"message/rfc822", attachment.content_type)
    ok_(attachment.is_attachment())

    # now guess by file name
    attachment = create.attachment(
        u"application/octet-stream", MULTIPART, "message.eml", u"attachment")
    eq_(u"message/rfc822", attachment.content_type)


def attaching_broken_emails_test():
    attachment = create.attachment(
        u"application/octet-stream", FALSE_MULTIPART, "message.eml", u"attachment")
    ok_(attachment.is_attachment())
    eq_(u"application/octet-stream", attachment.content_type)


def attaching_images_test():
    attachment = create.attachment(
        u"application/octet-stream", MAILGUN_PNG, "/home/alex/mailgun.png")
    eq_(u"image/png", attachment.content_type)


def attaching_text_test():
    attachment = create.attachment(
        u"application/octet-stream",
        u"Привет, как дела".encode(u"koi8-r"), "/home/alex/hi.txt")
    eq_(u"text/plain", attachment.content_type)
    eq_(u"Привет, как дела", attachment.body)


def guessing_text_encoding_test():
    text = create.text(u"plain", "hello", u"utf-8")
    eq_(u'ascii', text.charset)

    text = create.text(u"plain", u"hola, привет", u"utf-8")
    eq_(u'utf-8', text.charset)


def create_long_lines_test():
    val = "hello" * 1024
    text = create.text(u"plain", val, u"utf-8")
    eq_(u'ascii', text.charset)

    create.from_string(text.to_string())
    eq_(val, text.body)


def create_newlines_in_headers_test():
    text = create.text(u"plain", 'yo', u"utf-8")
    text.headers[b'Subject'] = 'Hello,\nnewline\r\n\r\n'
    text.headers.add(b'To', u'\n\nПревед, медвед\n!\r\n')

    text = create.from_string(text.to_string())
    eq_('Hello,newline', text.headers[b'Subject'])
    eq_(u'Превед, медвед!', text.headers[b'To'])


def unicode_quoted_printable_body_test():
    m = create.from_string(UNICODE_BODY)
    assert('ج' in m.parts[1].body)

