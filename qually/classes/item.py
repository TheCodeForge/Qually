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

    child_relationships=relationship("ItemRelationship", primaryjoin="ItemRelationship.parent_id==Item.id")
    parent_relationships=relationship("ItemRelationship", primaryjoin="ItemRelationship.child_id==Item.id")

    _name="ITEM"

    @property
    @lazy
    def parents(self):
        return [x.parent for x in self.parent_relationships]

    @property
    @lazy
    def children(self):
        return [x.child for x in self.child_relationships]

    @classmethod
    @org_lang
    def _kinds(cls):
        return {
            1: "Part",
            2: "Standard Operating Procedure",
            3: "Work Instruction"
        }

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
    def _transitions(self):
        return {}

    @classmethod
    def _layout():
        return eval("ItemRevision._layout()")

    @property
    @lazy
    def current_revision(self):
        return self.revisions.filter_by(_status=1).first()
    

class ItemRevision(Base, core_mixin, process_mixin):

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

    @classmethod
    def _layout(cls):
        return {
            0: [
                {
                    "name":_("Name"),
                    "value":"object_name",
                    "kind": "text"
                },
                {
                    "name": _("Description"),
                    "value":"object_description",
                    "kind": "multi"
                }
            ]
        }

ItemRevision._cols()
    

class ItemRelationship(Base, core_mixin):

    __tablename__="itemrelationship"

    id=Column(Integer, primary_key=True)
    parent_id=Column(Integer, ForeignKey(Item.id))
    child_id=Column(Integer, ForeignKey(Item.id))
    quantity=Column(Integer)

    parent=relationship("Item", primaryjoin="ItemRelationship.parent_id==Item.id", lazy="joined")
    child=relationship("Item", primaryjoin="ItemRelationship.child_id==Item.id", lazy="joined")

class ItemLog(Base, core_mixin):

    __tablename__="item_audit"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("item.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    created_ip=Column(String(64))

    key=Column(String)
    value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)