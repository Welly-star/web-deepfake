import os
import sys
import json
import urllib.parse

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

def vercel_handler(environ, start_response):
    # Debug inspect: jika URL ada ?debug=1
    query = environ.get('QUERY_STRING', '')
    if 'debug=1' in query:
        debug_info = {
            'PATH_INFO': environ.get('PATH_INFO'),
            'REQUEST_URI': environ.get('REQUEST_URI'),
            'RAW_URI': environ.get('RAW_URI'),
            'QUERY_STRING': query,
            'HTTP_X_MATCHED_PATH': environ.get('HTTP_X_MATCHED_PATH'),
            'HTTP_X_FORWARDED_URI': environ.get('HTTP_X_FORWARDED_URI'),
            'headers': {k: v for k, v in environ.items() if k.startswith('HTTP_')}
        }
        data = json.dumps(debug_info, indent=2).encode('utf-8')
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [data]

    return app(environ, start_response)

# Vercel entrypoint
app_handler = vercel_handler
app.wsgi_app = vercel_handler
