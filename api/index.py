import os
import sys
import urllib.parse

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Simpan original wsgi_app Flask agar tidak ada rekursi
original_wsgi_app = app.wsgi_app

def vercel_handler(environ, start_response):
    query = environ.get('QUERY_STRING', '')
    
    # Ambil path asli dari parameter __path__ yang dikirim oleh vercel.json
    if '__path__=' in query:
        params = urllib.parse.parse_qs(query, keep_blank_values=True)
        if '__path__' in params and params['__path__']:
            target_path = params['__path__'][0]
            if not target_path.startswith('/'):
                target_path = '/' + target_path
            environ['PATH_INFO'] = target_path
            # Hapus __path__ agar request.args tetap bersih
            del params['__path__']
            environ['QUERY_STRING'] = urllib.parse.urlencode(params, doseq=True)

    environ['SCRIPT_NAME'] = ''
    return original_wsgi_app(environ, start_response)

app.wsgi_app = vercel_handler
