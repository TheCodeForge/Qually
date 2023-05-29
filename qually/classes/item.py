from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x


class Item(Base, core_mixin, process_mixin):

    __tablename__="item"

    id=Column(Integer, primary_key=True)
    created_utc=Column(Integer)

    revisions=relationship("ItemRevision", lazy="dynamic", order_by="ItemRevision.id.desc()")

    @property
    def _lifecycle(self):
        return {
            0: {
                'name': _("Draft"),
                'users': [self.owner],
                'files': True
                },
            1: {
                'name': _("Design"),
                'users': []
                },
            2: {
                'name': _("Production"),
                'users': []
                },
            100: {
                'name': _("Obsolete"),
                'users': []
                }
        }

    @property
    @lazy
    def _transitions(self):
        return {}

    @property
    @lazy
    def current_revision(self):
        return self.revisions.filter_by(_status=1).first()
    

class ItemRevision(Base, core_mixin):

    __tablename__="itemrevision"

    id=Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    item_id=Column(Integer, ForeignKey(Item.id))
    file_id=Column(Integer, ForeignKey("files.id"))

    _status=Column(Integer, default=0)


    @property
    def _lifecycle(self):
        return {
            0:_("Proposed"),
            1:_("Effective"),
            2:_("Superceded")
        }

    @property
    def status(self):
        return self._lifecycle[self._status]
    

