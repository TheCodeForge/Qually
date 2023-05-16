from flask import request, g
import time
try:
    from flask_babel import format_datetime
except ModuleNotFoundError:
    pass
import datetime

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
        return format_datetime(datetime.datetime.fromtimestamp(self.created_utc), "dd MMMM yyyy")

    @property
    @lazy
    def created_datetime(self):
        return format_datetime(datetime.datetime.fromtimestamp(self.created_utc), "dd MMMM yyyy HH:mm")

    @property
    @lazy
    def available_transitions(self):

        tsns=self._transitions[self._status]

        return [x for x in tsns if tsns]
    