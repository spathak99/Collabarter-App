import os
import sys
from google.appengine.ext import vendor
vendor.add('lib')
on_appengine = os.environ.get('SERVER_SOFTWARE','').startswith('Development')
if on_appengine and os.name == 'nt':
    import ctypes
    os.name = None