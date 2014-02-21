import json

def json_response(start_response, val, http_header='200 OK'):
    start_response(http_header, [('Content-Type', 'application/json')])

    return [json.dumps(val) + '\n']
