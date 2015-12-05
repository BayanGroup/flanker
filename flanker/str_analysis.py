from __future__ import absolute_import
import json
import re
from collections import defaultdict, deque

import _sre
import yaml
import redis
import six

ACTIVE = False

if ACTIVE:
    sta_data = {}

    def str_representer(dumper, data):
        return dumper.represent_scalar('!t', str(data))

    yaml.add_representer(set, str_representer)
    yaml.add_representer(type, str_representer)

    try:
        redis_client = redis.Redis()
    except:
        pass

    retype = type(re.compile('A'))

def staf(var):
    pass


def statype(var):
    if var is None:
        return 'none'
    elif isinstance(var, tuple):
        return "(" + ", ".join([statype(x) for x in var]) + ")"
    elif isinstance(var, list):
        return "list(" + ", ".join(list(set(statype(x) for x in var))) + ")"
    elif isinstance(var, deque):
        return "deque(" + ", ".join(list(set(statype(x) for x in var))) + ")"
    elif isinstance(var, six.binary_type):
        try:
            var.decode('ascii')
            return 'str/a'
        except:
            return 'str'
    elif isinstance(var, six.text_type):
        try:
            var.encode('ascii')
            return 'uc/a'
        except:
            return 'uc'
    elif isinstance(var, retype):
        if isinstance(var.pattern, six.text_type) and var.flags & re.UNICODE > 0:
            return 're/uu'
        elif isinstance(var.pattern, six.text_type) and var.flags & re.UNICODE == 0:
            return 're/u-'
        elif isinstance(var.pattern, six.binary_type) and var.flags & re.UNICODE > 0:
            return 're/b?'
        elif isinstance(var.pattern, six.binary_type) and var.flags & re.UNICODE == 0:
            return 're/b-'
        else:
            return 're/??'
    else:
        return str(type(var))


def star(var):
    import inspect

    class SetEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, set):
                return str(o)
            if isinstance(o, type):
                return str(o)
            return json.JSONEncoder.default(self, o)

    frame = inspect.currentframe()
    this_frame = frame

    #caller_list = []
    # while frame.f_back:
    #     caller_list.append('{0}()'.format(frame.f_code.co_name))
    #     frame = frame.f_back
    # callers = '/'.join(reversed(caller_list))

    caller_line = "%s:%s (%s)" % (this_frame.f_back.f_code.co_filename, this_frame.f_back.f_lineno,
                                  this_frame.f_back.f_code.co_name)

    if caller_line not in sta_data:
        sta_data[caller_line] = defaultdict(int)
    sta_c = sta_data[caller_line]

    sta_c[statype(var)] += 1

    redis_client.set('vvs', json.dumps(sta_data, cls=SetEncoder))


if ACTIVE:
    sta = star
else:
    sta = staf
