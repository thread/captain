import re
import json
import urlparse

from .exceptions import Http404

re_upload = re.compile(r'^/(?P<repo>[-a-zA-Z0-9_]+)$')

def parse_repo(env):
    m = re_upload.match(env['PATH_INFO'])

    if m is None:
        raise Http404()

    return m.group('repo')

def json_response(start_response, val, http_header='200 OK'):
    start_response(http_header, [('Content-Type', 'application/json')])

    return [json.dumps(val) + '\n']

def parse_querystring(env):
    result = {}

    for k, v in urlparse.parse_qsl(env.get('QUERY_STRING', '')):
        # Always use the last value
        result[k] = v

    return result
