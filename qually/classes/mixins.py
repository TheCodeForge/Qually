from qually.helpers.base36 import *
from qually.helpers.lazy import lazy

class core_mixin():

    @property
    @lazy
    def base36id(self):

        return base36encode(self.id)

    @property
    @lazy
    def permalink_full(self):
        return f"http{'s' if app.config['FORCE_HTTPS'] else ''}://{app.config['SERVER_NAME']}{self.permalink}"

    @property
    @lazy
    def age(self):
        return g.timestamp - self.created_utc