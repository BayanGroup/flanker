# coding:utf-8

from os.path import join, abspath, dirname, exists
from nose.tools import *
import codecs


def fixtures_path():
    return join(abspath(dirname(__file__)), "fixtures")

def fixture_file(name):
    return join(fixtures_path(), name)

def skip_if_asked():
    from nose import SkipTest
    import sys
    if "--no-skip" not in sys.argv:
        raise SkipTest()


# mime fixture files
BOUNCE = open(fixture_file("messages/bounce/zed.eml"), 'rb').read()
MAILBOX_FULL = open(fixture_file("messages/bounce/mailbox-full.eml"), 'rb').read()
NDN = open(fixture_file("messages/bounce/delayed.eml"), 'rb').read()
NDN_BROKEN = open(fixture_file("messages/bounce/delayed-broken.eml"), 'rb').read()

SIGNED_FILE = open(fixture_file("messages/signed.eml"), 'rb')
SIGNED = open(fixture_file("messages/signed.eml"), 'rb').read()
LONG_LINKS = open(fixture_file("messages/long-links.eml"), 'rb').read()
MULTI_RECEIVED_HEADERS = open(
    fixture_file("messages/multi-received-headers.eml"), 'rb').read()
MAILGUN_PNG = open(fixture_file("messages/attachments/mailgun.png"), 'rb').read()
MAILGUN_WAV = open(
    fixture_file("messages/attachments/mailgun-rocks.wav"), 'rb').read()

TORTURE = open(fixture_file("messages/torture.eml"), 'rb').read()
TORTURE_PART = open(fixture_file("messages/torture-part.eml"), 'rb').read()
BILINGUAL = open(fixture_file("messages/bilingual-simple.eml"), 'rb').read()
RELATIVE = open(fixture_file("messages/relative.eml"), 'rb').read()
IPHONE = open(fixture_file("messages/iphone.eml"), 'rb').read()

MULTIPART = open(fixture_file("messages/multipart.eml"), 'rb').read()
FROM_ENCODING = open(fixture_file("messages/from-encoding.eml"), 'rb').read()
NO_CTYPE = open(fixture_file("messages/no-ctype.eml"), 'rb').read()
APACHE_MIME_MESSAGE_NEWS = open(fixture_file("messages/apache-message-news-mime.eml"), 'rb').read()
ENCLOSED = open(fixture_file("messages/enclosed.eml"), 'rb').read()
ENCLOSED_BROKEN_BOUNDARY = open(
    fixture_file("messages/enclosed-broken.eml"), 'rb').read()
ENCLOSED_ENDLESS = open(
    fixture_file("messages/enclosed-endless.eml"), 'rb').read()
ENCLOSED_BROKEN_BODY = open(
    fixture_file("messages/enclosed-broken-body.eml"), 'rb').read()
ENCLOSED_BROKEN_ENCODING = open(
    fixture_file("messages/enclosed-bad-encoding.eml"), 'rb').read()
FALSE_MULTIPART = open(
    fixture_file("messages/false-multipart.eml"), 'rb').read()
ENCODED_HEADER = open(
    fixture_file("messages/encoded-header.eml"), 'rb').read()
MESSAGE_EXTERNAL_BODY= open(
    fixture_file("messages/message-external-body.eml"), 'rb').read()
EIGHT_BIT = open(fixture_file("messages/8bitmime.eml"), 'rb').read()
BIG = open(fixture_file("messages/big.eml"), 'rb').read()
RUSSIAN_ATTACH_YAHOO = open(
    fixture_file("messages/russian-attachment-yahoo.eml"), 'rb').read()
QUOTED_PRINTABLE = open(
    fixture_file("messages/quoted-printable.eml"), 'rb').read()
TEXT_ONLY = open(fixture_file("messages/text-only.eml"), 'rb').read()
MAILGUN_PIC = open(fixture_file("messages/mailgun-pic.eml"), 'rb').read()
BZ2_ATTACHMENT  = open(fixture_file("messages/bz2-attachment.eml"), 'rb').read()
OUTLOOK_EXPRESS = open(fixture_file("messages/outlook-express.eml"), 'rb').read()

AOL_FBL = open(fixture_file("messages/complaints/aol.eml"), 'rb').read()
YAHOO_FBL = open(fixture_file("messages/complaints/yahoo.eml"), 'rb').read()
NOTIFICATION = open(fixture_file("messages/bounce/no-mx.eml"), 'rb').read()
DASHED_BOUNDARIES = open(
    fixture_file("messages/dashed-boundaries.eml"), 'rb').read()
WEIRD_BOUNCE = open(fixture_file("messages/bounce/gmail-no-dns.eml"), 'rb').read()
WEIRD_BOUNCE_2 = open(
    fixture_file("messages/bounce/gmail-invalid-address.eml"), 'rb').read()

WEIRD_BOUNCE_3 = open(
    fixture_file("messages/bounce/broken-mime.eml"), 'rb').read()
MISSING_BOUNDARIES = open(
    fixture_file("messages/missing-boundaries.eml"), 'rb').read()
MISSING_FINAL_BOUNDARY = open(
    fixture_file("messages/missing-final-boundary.eml"), 'rb').read()
DISPOSITION_NOTIFICATION = open(
    fixture_file("messages/disposition-notification.eml"), 'rb').read()
MAILFORMED_HEADERS = open(
    fixture_file("messages/mailformed-headers.eml"), 'rb').read()

SPAM_BROKEN_HEADERS = open(
    fixture_file("messages/spam/broken-headers.eml"), 'rb').read()
SPAM_BROKEN_CTYPE = open(
    fixture_file("messages/spam/broken-ctype.eml"), 'rb').read()
LONG_HEADER = open(
    fixture_file("messages/long-header.eml"), 'rb').read()
ATTACHED_PDF = open(fixture_file("messages/attached-pdf.eml"), 'rb').read()



# addresslib fixture files
MAILBOX_VALID_TESTS = open(fixture_file("mailbox_valid.txt"), 'rb').read()
MAILBOX_INVALID_TESTS = open(fixture_file("mailbox_invalid.txt"), 'rb').read()
ABRIDGED_LOCALPART_VALID_TESTS = open(fixture_file("abridged_localpart_valid.txt"), 'rb').read()
ABRIDGED_LOCALPART_INVALID_TESTS = open(fixture_file("abridged_localpart_invalid.txt"), 'rb').read()
URL_VALID_TESTS = codecs.open(fixture_file("url_valid.txt"), encoding='utf-8', mode='r').read()
URL_INVALID_TESTS = codecs.open(fixture_file("url_invalid.txt"), encoding='utf-8', mode='r').read()

DOMAIN_TYPO_VALID_TESTS = open(fixture_file("domain_typos_valid.txt"), 'rb').read()
DOMAIN_TYPO_INVALID_TESTS = open(fixture_file("domain_typos_invalid.txt"), 'rb').read()
