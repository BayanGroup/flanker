""" Useful wrappers for headers with parameters,
provide some convenience access methods
"""
from __future__ import absolute_import

import regex as re
import six

import flanker.addresslib.address

from email.utils import make_msgid

from flanker.str_analysis import sta


class WithParams(tuple):

    def __new__(self, value, params=None):
        return tuple.__new__(self, (value, params or {}))

    @property
    def value(self):
        return tuple.__getitem__(self, 0)

    @property
    def params(self):
        return tuple.__getitem__(self, 1)


@six.python_2_unicode_compatible
class ContentType(tuple):

    def __new__(self, main, sub, params=None):
        sta((main, sub))  # {u'(str/a, str/a)': 3513}
        return tuple.__new__(
            self, (main.lower() + u'/' + sub.lower(), params or {}))

    def __init__(self, main, sub, params={}):
        sta((main, sub))  # {u'(str/a, str/a)': 3513}
        self.main = main
        self.sub = sub

    @property
    def value(self):
        return tuple.__getitem__(self, 0)

    @property
    def params(self):
        return tuple.__getitem__(self, 1)

    @property
    def format_type(self):
        return tuple.__getitem__(self, 0).split(u'/')[0]

    @property
    def subtype(self):
        return tuple.__getitem__(self, 0).split(u'/')[1]

    def is_content_type(self):
        return True

    def is_boundary(self):
        return False

    def is_end(self):
        return False

    def is_singlepart(self):
        return self.main != u'multipart' and\
            self.main != u'message' and\
            not self.is_headers_container()

    def is_multipart(self):
        return self.main == u'multipart'

    def is_headers_container(self):
        return self.is_feedback_report() or \
            self.is_rfc_headers() or \
            self.is_message_external_body() or \
            self.is_disposition_notification()

    def is_rfc_headers(self):
        return self == u'text/rfc822-headers'

    def is_message_external_body(self):
        return self == u'message/external-body'

    def is_message_container(self):
        return self == u'message/rfc822' or self == 'message/news'

    def is_disposition_notification(self):
        return self == u'message/disposition-notification'

    def is_delivery_status(self):
        return self == u'message/delivery-status'

    def is_feedback_report(self):
        return self == u'message/feedback-report'

    def is_delivery_report(self):
        return self == u'multipart/report'

    def get_boundary(self):
        return self.params.get(u"boundary")

    def get_boundary_line(self, final=False):
        return u"--" + self.get_boundary() + (u"--" if final else u"")

    def get_charset(self):
        default = u'ascii' if self.main == u'text' else None
        c = self.params.get(u"charset", default)
        if c:
            c = c.lower()
        return c

    def set_charset(self, value):
        self.params[u"charset"] = value.lower()

    def __str__(self):
        return self.main + u"/" + self.sub

    def __eq__(self, other):
        if isinstance(other, ContentType):
            return self.main == other.main \
                and self.sub == other.sub \
                and self.params == other.params
        elif isinstance(other, tuple):
            return tuple.__eq__(self, other)
        elif isinstance(other, six.text_type):
            return str(self) == other
        elif isinstance(other, six.binary_type):
            return str(self).encode('utf-8') == other
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return u"ContentType('{}', '{}', {!r})".format(self.main, self.sub,
                                                      self.params)


class MessageId(six.text_type):

    RE_ID = re.compile(u"<([^<>]+)>", re.I)
    MIN_LENGTH = 5
    MAX_LENGTH = 256

    def __new__(cls, *args, **kw):
        sta(args)  # {u'(uc/a)': 95}
        return six.text_type.__new__(cls, *args, **kw)

    def __clean(self):
        sta(self)  # {u'str/a': 164}
        return self.replace(u'"', u'').replace(u"'", u'')

    def __hash__(self):
        return hash(self.__clean())

    def __eq__(self, other):
        if isinstance(other, MessageId):
            return self.__clean() == other.__clean()
        else:
            return self.__clean() == six.text_type(other)

    @classmethod
    def from_string(cls, string):
        sta(string)  # {u'uc/a': 86}
        if not isinstance(string, (str, six.text_type)):
            return None
        for message_id in cls.scan(string):
            return message_id

    @classmethod
    def generate(cls, domain=None):
        sta(domain)
        message_id = make_msgid().strip(u"<>")
        if domain:
            local = message_id.split(u'@')[0]
            message_id = local + u'@' + domain
        return cls(message_id)

    @classmethod
    def is_valid(cls, s):
        sta(s)  # {u'str/a': 1, u'uc/a': 6}
        return cls.MIN_LENGTH < len(s) < cls.MAX_LENGTH and \
            flanker.addresslib.address.is_email(s)

    @classmethod
    def scan(cls, string):
        sta(string)  # {u'uc/a': 140}
        for m in cls.RE_ID.finditer(string):
            message_id = m.group(1)
            if cls.is_valid(message_id):
                yield cls(message_id)


class Subject(six.text_type):
    RE_RE = re.compile(u"((RE|FW|FWD|HA)([[]\d])*:\s*)*", re.I)

    def __new__(cls, *args, **kw):
        sta(args)  # OK {u'(uc/a)': 1}
        return six.text_type.__new__(cls, *args, **kw)

    def strip_replies(self):
        sta(self)  # {u'uc/a': 1}
        return self.RE_RE.sub(u'', self)
