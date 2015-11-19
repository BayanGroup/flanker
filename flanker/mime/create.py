""" This package is a set of utilities and methods for building mime messages """
from __future__ import absolute_import

import uuid
from flanker.mime import DecodingError
from flanker.mime.message import ContentType, utils
from flanker.mime.message.part import MimePart, Body, Part, adjust_content_type
from flanker.mime.message import scanner
from flanker.mime.message.headers.parametrized import fix_content_type
from flanker.mime.message.headers import WithParams
from flanker.str_analysis import sta


def multipart(subtype):
    return MimePart(
        container=Part(
            ContentType(
                "multipart", subtype, {"boundary": uuid.uuid4().hex})),
        is_root=True)


def message_container(message):
    # sta(message) /
    part = MimePart(
        container=Part(ContentType("message", "rfc822")),
        enclosed=message)
    message.set_root(False)
    return part


def text(subtype, body, charset=None, disposition=None, filename=None):
    sta(subtype)  # {u'str/a': 70}
    sta(body)  # {u'str': 1, u'str/a': 61, u'uc': 7, u'uc/a': 1}
    return MimePart(
        container=Body(
            content_type=ContentType("text", subtype),
            body=body,
            charset=charset,
            disposition=disposition,
            filename=filename),
        is_root=True)


def binary(maintype, subtype, body, filename=None,
           disposition=None, charset=None, trust_ctype=False):
    sta(subtype)  # {u'str/a': 10}
    sta(body)  # {u'str': 6, u'str/a': 4}
    return MimePart(
        container=Body(
            content_type=ContentType(maintype, subtype),
            trust_ctype=trust_ctype,
            body=body,
            charset=charset,
            disposition=disposition,
            filename=filename),
        is_root=True)


def attachment(content_type, body, filename=None,
               disposition=None, charset=None):
    """Smarter method to build attachments that detects the proper content type
    and form of the message based on content type string, body and filename
    of the attachment
    """
    sta(content_type)  # {u'str/a': 5}
    sta(body)  # {u'str': 2, u'str/a': 3}

    # fix and sanitize content type string and get main and sub parts:
    main, sub = fix_content_type(
        content_type, default=('application', 'octet-stream'))

    # adjust content type based on body or filename if it's not too accurate
    content_type = adjust_content_type(
        ContentType(main, sub), body, filename)

    if content_type.main == 'message':
        try:
            message = message_container(from_string(body))
            message.headers['Content-Disposition'] = WithParams(disposition)
            return message
        except DecodingError:
            content_type = ContentType('application', 'octet-stream')
    return binary(
        content_type.main,
        content_type.sub,
        body, filename,
        disposition,
        charset, True)


def from_string(string):
    sta(string)  # {u"<type 'type'>": 1, u'list()': 1, u'none': 1, u'str/a': 24}
    return scanner.scan(string)


def from_python(message):
    sta(utils.python_message_to_string(message))  # {u'str/a': 1}
    return from_string(
        utils.python_message_to_string(message))


def from_message(message):
    sta(message.to_string())  # {u'str/a': 1}
    return from_string(message.to_string())
