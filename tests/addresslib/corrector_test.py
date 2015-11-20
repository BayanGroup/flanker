from __future__ import absolute_import
from __future__ import print_function
# coding:utf-8

import re
import string
import random

from six import int2byte

from .. import *

from nose.tools import assert_equal, assert_not_equal, ok_
from nose.tools import nottest

from flanker.addresslib import validate
from flanker.addresslib import corrector
from six.moves import range
from six.moves import zip


COMMENT = re.compile(b'''\s*#''')


@nottest
def generate_mutated_string(source_str, num):
    letters = list(bytearray(source_str))
    rchars = re.sub(b'[' + source_str + b'.' + b']', b'', string.ascii_lowercase.encode('ascii'))

    random_orig = random.sample(list(enumerate(bytearray(source_str))), num)
    random_new = random.sample(list(enumerate(bytearray(rchars))), num)

    for i, j in zip(random_orig, random_new):
        letters[i[0]] = j[1]

    return b''.join(int2byte(c) for c in letters)

@nottest
def generate_longer_string(source_str, num):
    letters = list(bytearray(source_str))
    rchars = re.sub(b'[' + source_str + b']', b'', string.ascii_lowercase.encode('ascii'))

    for i in range(num):
        letters = [random.choice(list(bytearray(rchars)))] + letters

    return b''.join(int2byte(c) for c in letters)

@nottest
def generate_shorter_string(source_str, num):
    return source_str[0:len(source_str)-num]

@nottest
def domain_generator(size=6, chars=string.ascii_letters + string.digits):
    chars = chars.encode('iso-8859-1')
    domain = b''.join(int2byte(random.choice(list(bytearray(chars)))) for x in range(size))
    return b''.join([domain, b'.com'])


def test_domain_typo_valid_set():
    sugg_correct = 0
    sugg_total = 0
    print('')

    for line in DOMAIN_TYPO_VALID_TESTS.split(b'\n'):
        # strip line, skip over empty lines
        line = line.strip()
        if line == b'':
            continue

        # skip over comments or empty lines
        match = COMMENT.match(line)
        if match:
            continue

        parts = line.split(b',')

        test_str = b'username@' + parts[0]
        corr_str = b'username@' + parts[1]
        sugg_str = validate.suggest_alternate(test_str)

        if sugg_str == corr_str:
            sugg_correct += 1
        else:
            print('did not match: {0}, {1}'.format(test_str, sugg_str))

        sugg_total += 1

    # ensure that we have greater than 90% accuracy
    accuracy = float(sugg_correct) / sugg_total
    print('external valid: accuracy: {0}, correct: {1}, total: {2}'.\
        format(accuracy, sugg_correct, sugg_total))
    ok_(accuracy > 0.90)


def test_domain_typo_invalid_set():
    sugg_correct = 0
    sugg_total = 0
    print('')

    for line in DOMAIN_TYPO_INVALID_TESTS.split(b'\n'):
        # strip line, skip over empty lines
        line = line.strip()
        if line == b'':
            continue

        # skip over comments or empty lines
        match = COMMENT.match(line)
        if match:
            continue

        test_str = b'username@' + line
        sugg_str = validate.suggest_alternate(test_str)

        if sugg_str == None:
            sugg_correct += 1
        else:
            print('incorrect correction: {0}, {1}'.format(test_str, sugg_str))

        sugg_total += 1

    # ensure that we have greater than 90% accuracy
    accuracy = float(sugg_correct) / sugg_total
    print('external invalid: accuracy: {0}, correct: {1}, total: {2}'.\
        format(accuracy, sugg_correct, sugg_total))
    ok_(accuracy > 0.90)


# For the remaining tests, the accuracy is significantly lower than
# the above because the corrector is tuned to real typos that occur,
# while what we have below are random mutations. Also, because
# this these test are non-deterministic, it's better to have a lower
# lower threshold to ensure that tests don't fail dring deployment
# due to a outlier). Realistic numbers for all thees tests should easily
# be above 80% accuracy range.

def test_suggest_alternate_mutations_valid():
    sugg_correct = 0
    sugg_total = 0
    print('')

    for i in range(1, 3):
        for j in range(100):
            domain = random.choice(corrector.MOST_COMMON_DOMAINS)
            orig_str = b'username@' + domain

            mstr = b'username@' + generate_mutated_string(domain, i)
            sugg_str = validate.suggest_alternate(mstr)
            if sugg_str == orig_str:
                sugg_correct += 1

            sugg_total += 1

    # ensure that we have greater than 60% accuracy
    accuracy = float(sugg_correct) / sugg_total
    print('mutations valid: accuracy: {0}, correct: {1}, total: {2}'.\
        format(accuracy, sugg_correct, sugg_total))
    ok_(accuracy > 0.60)


def test_suggest_alternate_longer_valid():
    sugg_correct = 0
    sugg_total = 0
    print('')

    for i in range(1, 3):
        for j in range(100):
            domain = random.choice(corrector.MOST_COMMON_DOMAINS)
            orig_str = b'username@' + domain

            lstr = b'username@' + generate_longer_string(domain, i)
            sugg_str = validate.suggest_alternate(lstr)
            if sugg_str == orig_str:
                sugg_correct += 1

            sugg_total += 1

    # ensure that we have greater than 60% accuracy
    accuracy = float(sugg_correct) / sugg_total
    print('longer valid: accuracy: {0}, correct: {1}, total: {2}'.\
        format(accuracy, sugg_correct, sugg_total))
    ok_(accuracy > 0.60)


def test_suggest_alternate_shorter_valid():
    sugg_correct = 0
    sugg_total = 0
    print('')

    for i in range(1, 3):
        for j in range(100):
            domain = random.choice(corrector.MOST_COMMON_DOMAINS)
            orig_str = b'username@' + domain

            sstr = b'username@' + generate_shorter_string(domain, i)
            sugg_str = validate.suggest_alternate(sstr)
            if sugg_str == orig_str:
                sugg_correct += 1

            sugg_total += 1

    # ensure that we have greater than 60% accuracy
    accuracy = float(sugg_correct) / sugg_total
    print('shorter valid: accuracy: {0}, correct: {1}, total: {2}'.\
        format(accuracy, sugg_correct, sugg_total))
    ok_(accuracy > 0.60)


def test_suggest_alternate_invalid():
    sugg_correct = 0
    sugg_total = 0
    print('')

    for i in range(3, 10):
        for j in range(100):
            domain = domain_generator(i)

            orig_str = b'username@' + domain
            sugg_str = validate.suggest_alternate(orig_str)
            if sugg_str == None:
                sugg_correct += 1
            else:
                print('did not match: {0}, {1}'.format(orig_str, sugg_str))

            sugg_total += 1

    # ensure that we have greater than 60% accuracy
    accuracy = float(sugg_correct) / sugg_total
    print('alternative invalid: accuracy: {0}, correct: {1}, total: {2}'.\
        format(accuracy, sugg_correct, sugg_total))
    ok_(accuracy > 0.60)
