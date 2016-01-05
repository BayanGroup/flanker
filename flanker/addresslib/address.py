# coding:utf-8

"""
Public interface for flanker address (email or url) parsing and validation
capabilities.

Public Functions in flanker.addresslib.address module:

    * parse(address, addr_spec_only=False)

      Parse a single address or URL. Can parse just the address spec or the
      full mailbox.

    * parse_list(address_list, strict=False, as_tuple=False)

      Parse a list of addresses, operates in strict or relaxed modes. Strict
      mode will fail at the first instance of invalid grammar, relaxed modes
      tries to recover and continue.

    * validate_address(addr_spec)

      Validates (parse, plus dns, mx check, and custom grammar) a single
      address spec. In the case of a valid address returns an EmailAddress
      object, otherwise returns None.

    * validate_list(addr_list, as_tuple=False)

      Validates an address list, and returns a tuple of parsed and unparsed
      portions.

When valid addresses are returned, they are returned as an instance of either
EmailAddress or UrlAddress in flanker.addresslib.address.

See the parser.py module for implementation details of the parser.
"""
from __future__ import absolute_import

import time
import flanker.addresslib.parser
from flanker.addresslib.quote import smart_unquote, smart_quote
import flanker.addresslib.validate

from flanker.addresslib.parser import MAX_ADDRESS_LENGTH
from flanker.utils import is_pure_ascii
from flanker.str_analysis import sta, statype
from flanker.utils import metrics_wrapper
from flanker.mime.message.headers.encoding import encode_string
from flanker.mime.message.headers.encodedword import mime_to_unicode
from six.moves.urllib.parse import urlparse
import six


@metrics_wrapper()
def parse(address, addr_spec_only=False, metrics=False):
    """
    Given a string, returns a scalar object representing a single full
    mailbox (display name and addr-spec), addr-spec, or a url.

    Returns an Address object and optionally metrics on processing
    time if requested.

    Examples:
        >>> address.parse('John Smith <john@smith.com')
        John Smith <john@smith.com>

        >>> print address.parse('John <john@smith.com>', addr_spec_only=True)
        None

        >>> print address.parse('john@smith.com', addr_spec_only=True)
        'john@smith.com'

        >>> address.parse('http://host.com/post?q')
        http://host.com/post?q

        >>> print address.parse('foo')
        None
    """
    # sta(address)  # OK {u'none': 1, u'str': 1, u'str/a': 3480, u'uc': 238, u'uc/a': 132}
    mtimes = {'parsing': 0}

    parser = flanker.addresslib.parser._AddressParser(False)

    try:
        # addr-spec only
        if addr_spec_only:
            bstart = time.time()
            retval = parser.address_spec(address)
            mtimes['parsing'] = time.time() - bstart
            return retval, mtimes

        # full address
        bstart = time.time()
        retval = parser.address(address)
        mtimes['parsing'] = time.time() - bstart
        return retval, mtimes

    # supress any exceptions and return None
    except flanker.addresslib.parser.ParserException:
        return None, mtimes


@metrics_wrapper()
def parse_list(address_list, strict=False, as_tuple=False, metrics=False):
    """
    Given an string or list of email addresses and/or urls seperated by a
    delimiter (comma (,) or semi-colon (;)), returns an AddressList object
    (an iterable list representing parsed email addresses and urls).

    The Parser operates in strict or relaxed modes. In strict mode the parser
    will quit at the first occurrence of error, in relaxed mode the parser
    will attempt to seek to to known valid location and continue parsing.

    The parser can return a list of parsed addresses or a tuple containing
    the parsed and unparsed portions. The parser also returns the parsing
    time metrics if requested.

    Examples:
        >>> address.parse_list('A <a@b>')
        [A <a@b>]

        >>> address.parse_list('A <a@b>, C <d@e>')
        [A <a@b>, C <d@e>]

        >>> address.parse_list('A <a@b>, C, D <d@e>')
        [A <a@b>, D <d@e>]

        >>> address.parse_list('A <a@b>, C, D <d@e>')
        [A <a@b>]

        >>> address.parse_list('A <a@b>, D <d@e>, http://localhost')
        [A <a@b>, D <d@e>, http://localhost]
    """
    # sta(address_list)  # OK {u"<type 'list'>": 1600, u'str/a': 1627, u'uc': 1}
    mtimes = {'parsing': 0}
    parser = flanker.addresslib.parser._AddressParser(strict)

    # if we have a list, transform it into a string first
    if isinstance(address_list, list):
        # sta(address_list)  # OK {u'list()': 20, u"list(<class 'flanker.addresslib.address.EmailAddress'>)": 1574, u'list(str/a)': 5, u'list(str/a, uc)': 1}
        # sta(_normalize_address_list(address_list))  # OK {u'list()': 20, u'list(uc/a)': 1579, u'list(uc/a, uc)': 1}
        address_list = u', '.join(_normalize_address_list(address_list))
        #sta(address_list)  # OK {u'uc': 1, u'uc/a': 1599}

    # parse
    try:
        bstart = time.time()
        if strict:
            p = parser.address_list(address_list)
            u = []
        else:
            p, u = parser.address_list(address_list)
        mtimes['parsing'] = time.time() - bstart
    except flanker.addresslib.parser.ParserException:
        p, u = (AddressList(), [])

    # return as tuple or just parsed addresses
    if as_tuple:
        return p, u, mtimes
    return p, mtimes


@metrics_wrapper()
def validate_address(addr_spec, metrics=False):
    """
    Given an addr-spec, runs the pre-parser, the parser, DNS MX checks,
    MX existence checks, and if available, ESP specific grammar for the
    local part.

    In the case of a valid address returns an EmailAddress object, otherwise
    returns None. If requested, will also return the parsing time metrics.

    Examples:
        >>> address.validate_address('john@non-existent-domain.com')
        None

        >>> address.validate_address('user@gmail.com')
        None

        >>> address.validate_address('user.1234@gmail.com')
        user.1234@gmail.com
    """
    #sta(addr_spec)  # OK {u'str/a': 3039}
    mtimes = {'parsing': 0, 'mx_lookup': 0,
        'dns_lookup': 0, 'mx_conn':0 , 'custom_grammar':0}

    # sanity check
    if addr_spec is None:
        return None, mtimes
    if not is_pure_ascii(addr_spec):
        return None, mtimes

    # preparse address into its parts and perform any ESP specific pre-parsing
    addr_parts = flanker.addresslib.validate.preparse_address(addr_spec)
    if addr_parts is None:
        return None, mtimes

    # run parser against address
    bstart = time.time()
    # sta(addr_parts)  # OK {u'list(str/a)': 3039}
    paddr = parse(b'@'.join(addr_parts), addr_spec_only=True)
    mtimes['parsing'] = time.time() - bstart
    if paddr is None:
        return None, mtimes

    # lookup if this domain has a mail exchanger
    exchanger, mx_metrics = \
        flanker.addresslib.validate.mail_exchanger_lookup(addr_parts[-1], metrics=True)
    mtimes['mx_lookup'] = mx_metrics['mx_lookup']
    mtimes['dns_lookup'] = mx_metrics['dns_lookup']
    mtimes['mx_conn'] = mx_metrics['mx_conn']
    if exchanger is None:
        return None, mtimes

    # lookup custom local-part grammar if it exists
    bstart = time.time()
    plugin = flanker.addresslib.validate.plugin_for_esp(exchanger)
    mtimes['custom_grammar'] = time.time() - bstart
    if plugin and plugin.validate(addr_parts[0]) is False:
        return None, mtimes

    return paddr, mtimes


@metrics_wrapper()
def validate_list(addr_list, as_tuple=False, metrics=False):
    """
    Validates an address list, and returns a tuple of parsed and unparsed
    portions.

    Returns results as a list or tuple consisting of the parsed addresses
    and unparsable protions. If requested, will also return parisng time
    metrics.

    Examples:
        >>> address.validate_address_list('a@mailgun.com, c@mailgun.com')
        [a@mailgun.com, c@mailgun.com]

        >>> address.validate_address_list('a@mailgun.com, b@example.com')
        [a@mailgun.com]

        >>> address.validate_address_list('a@b, c@d, e@example.com', as_tuple=True)
        ([a@mailgun.com, c@mailgun.com], ['e@example.com'])
    """
    # sta(addr_list)  # OK {u'str/a': 12}
    mtimes = {'parsing': 0, 'mx_lookup': 0,
        'dns_lookup': 0, 'mx_conn':0 , 'custom_grammar':0}

    if addr_list is None:
        return None, mtimes

    # parse addresses
    bstart = time.time()
    parsed_addresses, unparseable = parse_list(addr_list, as_tuple=True)
    mtimes['parsing'] = time.time() - bstart

    plist = flanker.addresslib.address.AddressList()
    ulist = []

    # make sure parsed list pass dns and esp grammar
    for paddr in parsed_addresses:

        # lookup if this domain has a mail exchanger
        exchanger, mx_metrics = \
            flanker.addresslib.validate.mail_exchanger_lookup(paddr.hostname, metrics=True)
        mtimes['mx_lookup'] += mx_metrics['mx_lookup']
        mtimes['dns_lookup'] += mx_metrics['dns_lookup']
        mtimes['mx_conn'] += mx_metrics['mx_conn']

        if exchanger is None:
            ulist.append(paddr.full_spec())
            continue

        # lookup custom local-part grammar if it exists
        plugin = flanker.addresslib.validate.plugin_for_esp(exchanger)
        bstart = time.time()
        if plugin and plugin.validate(paddr.mailbox) is False:
            ulist.append(paddr.full_spec())
            continue
        mtimes['custom_grammar'] = time.time() - bstart

        plist.append(paddr)

    # loop over unparsable list and check if any can be fixed with
    # preparsing cleanup and if so, run full validator
    for unpar in unparseable:
        paddr, metrics = validate_address(unpar, metrics=True)
        if paddr:
            plist.append(paddr)
        else:
            ulist.append(unpar)

        # update all the metrics
        for k, v in six.iteritems(metrics):
            metrics[k] += v

    if as_tuple:
        return plist, ulist, mtimes
    return plist, mtimes


def is_email(string):
    # sta(string)  # OK {u'none': 1, u'str/a': 3}
    if parse(string, True):
        return True
    return False


class Address(object):
    """
    Base class that represents an address (email or URL). Use it to create
    concrete instances of different addresses:
    """

    @property
    def supports_routing(self):
        """
        Indicates that by default this address cannot be routed.
        """
        return False

    class Type(object):
        """
        Enumerates the types of addresses we support:
            >>> parse('foo@example.com').addr_type
            'email'

            >>> parse('http://example.com').addr_type
            'url'
        """
        Email = 'email'
        Url   = 'url'


# TODO: RFC 6530 (Internationalizaion of address, etc) compliancy
@six.python_2_unicode_compatible
class EmailAddress(Address):
    """
    Represents a fully parsed email address with built-in support for MIME
    encoding. Note, do not use EmailAddress class directly, use the parse()
    or parse_list() functions to return a scalar or iterable list respectively.

    Examples:
       >>> addr = EmailAddress("Bob Silva", "bob@host.com")
       >>> addr.address
       'bob@host.com'
       >>> addr.hostname
       'host.com'
       >>> addr.mailbox
       'bob'

    Display name is always returned in Unicode, i.e. ready to be displayed on
    web forms:

       >>> addr.display_name
       u'Bob Silva'

    And full email spec is 100% ASCII, encoded for MIME:
       >>> addr.full_spec()
       'Bob Silva <bob@host.com>'
    """

    __slots__ = ['display_name', 'mailbox', 'hostname', 'address']

    def __init__(self, display_name, spec=None, parsed_name=None):
        # sta(spec)  # OK {u'none': 13635, u'str/a': 132, u'uc/a': 33}
        # sta(parsed_name)  # OK {u'none': 13604, u'uc': 60, u'uc/a': 136}
        # sta(display_name)  # OK {u'none': 3, u'str/a': 8302, u'uc': 105, u'uc/a': 5390}
        if spec is None:
            spec = display_name
            display_name = None

        assert(spec)

        spec = spec if isinstance(spec, six.binary_type) else spec.encode('ascii')

        if parsed_name:
            self.display_name = smart_unquote(mime_to_unicode(parsed_name))
        elif display_name:
            self.display_name = display_name
        else:
            self.display_name = u''

        self.display_name = self.display_name if isinstance(self.display_name, six.text_type) else self.display_name.decode('ascii')

        parts = spec.rsplit(b'@', 1)
        self.mailbox = parts[0]
        self.hostname = parts[1].lower()
        self.address = self.mailbox + b"@" + self.hostname
        self.addr_type = self.Type.Email
        # sta(self.display_name)  # OK {u'uc': 213, u'uc/a': 13587}
        # sta(self.address)  # OK {u'str/a': 13800}
        # sta(self.hostname)  # OK {u'str/a': 13800}
        # sta(self.mailbox)  # OK {u'str/a': 13800}


    def __repr__(self):
        """
        >>> repr(EmailAddress("John Smith", "john@smith.com"))
        'John Smith <john@smith.com>'
        """
        # sta(self.full_spec())  # OK {}
        return self.full_spec().decode('ascii')

    def __str__(self):
        """
        >>> str(EmailAddress("boo@host.com"))
        'boo@host.com'
        """
        # sta(self.address)  # OK {u'str/a': 1}
        return self.address if isinstance(self.address, six.text_type) else self.address.decode('utf-8')

    @property
    def supports_routing(self):
        """
        Email addresses can be routed.
        """
        return True

    def full_spec(self):
        """
        Returns a full spec of an email address. Always in ASCII, RFC-2822
        compliant, safe to be included into MIME:

           >>> EmailAddress("Ev K", "ev@example.com").full_spec()
           'Ev K <ev@host.com>'
           >>> EmailAddress("Жека", "ev@example.com").full_spec()
           '=?utf-8?b?0JbQtdC60LA=?= <ev@example.com>'
        """
        if self.display_name:
            encoded_display_name = smart_quote(encode_string(
                None, self.display_name, maxlinelen=MAX_ADDRESS_LENGTH))
            # sta(encoded_display_name)  # OK {u'str/a': 113}
            return encoded_display_name + b' <' + self.address + b'>'
        return self.address

    def to_unicode(self):
        """
        Converts to unicode.
        """
        if self.display_name:
            return u'{0} <{1}>'.format(self.display_name, self.address.decode('ascii'))
        return u'{0}'.format(self.address.decode('ascii'))

    def __cmp__(self, other):
        return True

    def __eq__(self, other):
        """
        Allows comparison of two addresses.
        """
        if other:
            if isinstance(other, (six.text_type, six.binary_type)):
                other = parse(other)
                if not other:
                    return False
            return self.address.lower() == other.address.lower()
        return False

    def __ne__(self, other):
        """
        Negative comparison support
        """
        return not (self == other)


    def __hash__(self):
        """
        Hashing allows using Address objects as keys in collections and compare
        them in sets

            >>> a = Address.from_string("a@host")
            >>> b = Address.from_string("A <A@host>")
            >>> hash(a) == hash(b)
            True
            >>> s = set()
            >>> s.add(a)
            >>> s.add(b)
            >>> len(s)
            1
        """
        return hash(self.address.lower())


# TODO: Non-ASCII addresses compliancy
@six.python_2_unicode_compatible
class UrlAddress(Address):
    """
    Represents a parsed URL:
        >>> url = UrlAddress("http://user@host.com:8080?q=a")
        >>> url.hostname
        'host.com'
        >>> url.port
        8080
        >>> url.scheme
        'http'
        >>> str(url)
        'http://user@host.com:8080?q=a'

    Note: do not create UrlAddress class directly by passing raw "internet
    data", use the parse() and parse_list() functions instead.
    """

    __slots__ = ['address', 'parse_result']

    def __init__(self, spec):
        self.address = spec
        # sta(self.address)  # OK {u'str': 1, u'str/a': 24}
        self.parse_result = urlparse(spec)
        self.addr_type = self.Type.Url

    @property
    def hostname(self):
        hostname = self.parse_result.hostname
        # sta(hostname)  # OK {u'none': 1, u'str/a': 1}
        if hostname:
            return hostname.lower()

    @property
    def port(self):
        return self.parse_result.port

    @property
    def scheme(self):
        # sta(self.parse_result.path)  # OK {u'str/a': 1}
        return self.parse_result.scheme

    @property
    def path(self):
        return self.parse_result.path

    def __str__(self):
        return self.address if isinstance(self.address, six.text_type) else self.address.decode('utf-8')

    def full_spec(self):
        return self.address if isinstance(self.address, bytes) else self.address.encode('idna')

    def to_unicode(self):
        return self.address if isinstance(self.address, six.text_type) else self.address.decode('idna')

    def __repr__(self):
        return self.address.decode('utf-8')

    def __eq__(self, other):
        "Allows comparison of two URLs"
        if other:
            if not isinstance(other, (six.text_type, six.binary_type)):
                other = other.address
            return self.address == other

    def __hash__(self):
        return hash(self.address)


@six.python_2_unicode_compatible
class AddressList(object):
    """
    Keeps the list of addresses. Each address is an EmailAddress or
    URLAddress objectAddress-derived object.

    To create a list, use the parse_list method, do not create an
    AddressList directly.

    To see if the address is in the list:
        >>> "missing@host.com" in al
        False
        >>> "bob@host.COM" in al
        True
    """

    def __init__(self, container=None):
        if container is None:
            container = []
        self.container = container

    def append(self, n):
        self.container.append(n)

    def remove(self, n):
        self.container.remove(n)

    def __iter__(self):
        return iter(self.container)

    def __getitem__(self, key):
        return self.container[key]

    def __len__(self):
        return len(self.container)

    def __eq__(self, other):
        """
        When comparing ourselves to other lists we must ignore order.
        """
        if isinstance(other, list):
            other = parse_list(other)
        return set(self.container) == set(other.container)

    def __repr__(self):
        return ''.join(['[', self.full_spec().decode('utf-8'), ']'])

    def __add__(self, other):
        """
        Adding two AddressLists together yields another AddressList.
        """
        if isinstance(other, list):
            result = self.container + parse_list(other).container
        else:
            result = self.container + other.container
        return AddressList(result)

    def full_spec(self, delimiter=b", "):
        """
        Returns a full string which looks pretty much what the original was
        like
            >>> adl = AddressList("Foo <foo@host.com>, Bar <bar@host.com>")
            >>> adl.full_spec(delimiter=b'; ')
            'Foo <foo@host.com; Bar <bar@host.com>'
        """
        return delimiter.join(addr.full_spec() for addr in self.container)

    def to_unicode(self, delimiter=u", "):
        return delimiter.join(addr.to_unicode() for addr in self.container)

    def to_ascii_list(self):
        return [addr.full_spec() for addr in self.container]

    @property
    def addresses(self):
        """
        Returns a list of just addresses, i.e. no names:
            >>> adl = AddressList("Foo <foo@host.com>, Bar <bar@host.com>")
            >>> adl.addresses
            ['foo@host.com', 'bar@host.com']
        """
        return [addr.address for addr in self.container]

    def __str__(self):
        # sta(self.full_spec())  # OK {u'str/a': 2}
        f_spec = self.full_spec()
        return f_spec if isinstance(f_spec, six.text_type) else f_spec.decode('utf-8')

    @property
    def hostnames(self):
        """
        Returns a set of hostnames used in addresses in this list.
        """
        return set([addr.hostname for addr in self.container])

    @property
    def addr_types(self):
        """
        Returns a set of address types used in addresses in this list.
        """
        return set([addr.addr_type for addr in self.container])


def _normalize_address_list(address_list):
    # sta(address_list)  # OK {u"<type 'list'>": 3200}
    parts = []

    for addr in address_list:
        if isinstance(addr, Address):
            parts.append(addr.to_unicode())
            # sta(addr.to_unicode())  # OK {u'uc/a': 9398}
        elif isinstance(addr, six.text_type):
            parts.append(addr)
            # sta(addr)  # OK {u'uc': 2}
        elif isinstance(addr, six.binary_type):
            parts.append(addr.decode('ascii'))
            # sta(addr.decode('ascii'))  # OK {u'uc/a': 1156}

    return parts
