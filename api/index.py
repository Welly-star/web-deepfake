import os
import sys

# Tambahkan direktori root proyek ke sys.path agar app.py & model.py terbaca di Vercel
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# Vercel serverless function entrypoint

