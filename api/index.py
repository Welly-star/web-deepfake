import os
import sys
import urllib.parse

# Tambahkan direktori root proyek ke sys.path agar app.py & model.py terbaca di Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# WSGI Middleware untuk menormalkan PATH_INFO, QUERY_STRING & SCRIPT_NAME pada Vercel Serverless
class VercelPathFix:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        matched_path = environ.get('HTTP_X_MATCHED_PATH', '')

        real_path = None
        if '__path__=' in query_string:
            params = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            if '__path__' in params and params['__path__']:
                real_path = params['__path__'][0]
                del params['__path__']
                environ['QUERY_STRING'] = urllib.parse.urlencode(params, doseq=True)
        elif matched_path:
            real_path = matched_path

        if real_path:
            if not real_path.startswith('/'):
                real_path = '/' + real_path
            environ['PATH_INFO'] = real_path

        environ['SCRIPT_NAME'] = ''
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFix(app.wsgi_app)
