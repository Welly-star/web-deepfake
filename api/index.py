import os
import sys

# Tambahkan direktori root proyek ke sys.path agar app.py & model.py terbaca di Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# WSGI Middleware untuk menormalkan PATH_INFO pada Vercel Serverless
class VercelPathFix:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith('/api/index.py'):
            environ['PATH_INFO'] = path[len('/api/index.py'):] or '/'
        elif path.startswith('/api'):
            environ['PATH_INFO'] = path[len('/api'):] or '/'
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelPathFix(app.wsgi_app)
