import re
import json

from .exceptions import Http400

re_upload = re.compile(r'^/(?P<repo>[^/]+)$')

def parse_repo(env):
    m = re_upload.match(env['PATH_INFO'])

    if m is None:
        raise Http404()

    return m.group('repo')

def json_response(start_response, val, http_header='200 OK'):
    start_response(http_header, [('Content-Type', 'application/json')])

    return [json.dumps(val) + '\n']
