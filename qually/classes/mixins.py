from flask import request, g
import time

from qually.helpers.base36 import *
from qually.helpers.lazy import lazy

from qually.__main__ import app, Base

class core_mixin():

    @property
    @lazy
    def base36id(self):

        return base36encode(self.id)

    @property
    @lazy
    def permalink_full(self):
        return f"http{'s' if app.config['HTTPS'] else ''}://{app.config['SERVER_NAME']}{self.permalink}"

    @property
    @lazy
    def age(self):
        return g.time - self.created_utc

    @property
    @lazy
    def created_date(self):
        return time.strftime("%d %B %Y", time.gmtime(self.created_utc))

    @property
    @lazy
    def created_datetime(self):
        return time.strftime("%d %B %Y at %H:%M:%S UTC",
                             time.gmtime(self.created_utc))
