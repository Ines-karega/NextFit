"""Starting point for the live site on Vercel.

Vercel looks in the main folder for a file with one of a few fixed names (this is
one of them) that holds a Flask "app". Our app lives in the backend folder, so this
file only points to it. On your own computer you still start the site with:
    python backend/app.py
"""
import os
import sys

# Let Python find app.py, db.py and the other files inside the backend folder.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app import app  # noqa: E402  (this import must come after the line above)
