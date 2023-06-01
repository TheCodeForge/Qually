from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x


class Item(Base, core_mixin, process_mixin):

    __tablename__="item"

    id=Column(Integer, primary_key=True)
    _kind_id=Column(Integer, default=1)
    owner_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(BigInteger)
    number=Column(Integer, default=0)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    _status = Column(Integer, default=0)
    custom_number=Column(String)

    revisions=relationship("ItemRevision", lazy="dynamic", order_by="ItemRevision.id.desc()")

    owner=relationship("User")
    child_relationships=relationship("ItemRelationship", primaryjoin="ItemRelationship.parent_id==Item.id", backref="parent")
    parent_relationships=relationship("ItemRelationship", primaryjoin="ItemRelationship.child_id==Item.id", backref="child")

    _name="ITEM"

    __table_args__=(
            UniqueConstraint(
                '_kind_id',
                'number', 
                'organization_id',
                name=f'item_org_number_unique'
                ),
            )

    @classmethod
    def _next_number(cls):

        return g.user.organization.next_id(cls._kinds()[int(request.form.get('type'))]['orgname'])

    @classmethod
    def name_readable(cls):
        return _("Item")

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
            1: {
                'name': _("Part"),
                'orgname': 'part'
                },
            2: {
                'name': _("Standard Operating Procedure"),
                'orgname': 'sop'
                },
            3: {
                'name': _("Work Instruction"),
                'orgname': 'wi'
                }
        }

    @property
    def kind(self):
        return self._kinds()[self._kind_id]['name']

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
    @org_lang
    def _layout(cls):
        data = eval("ItemRevision._layout()")

        data =[
            {
                "name": _("Type"),
                "value":"type",
                "kind": "dropdown",
                "values": {x:cls._kinds()[x]['name'] for x in cls._kinds()}
            },
            {
                "name": _("Custom Number"),
                "value":"custom_number",
                "kind": "text",
                "placeholder": _("Leave blank to set item number automatically.")
            }
        ]+data
        
        return data

    @property
    @lazy
    def current_revision(self):
        return self.revisions.filter_by(_status=1).first()

    def __getattr__(self, attr):

        return getattr(self.current_revision, attr)

    def __setattr__(self, attr, value):

        return setattr(self.current_revision, attr, value)
    

class ItemRevision(Base, core_mixin):

    __tablename__="itemrevision"

    id=Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    item_id=Column(Integer, ForeignKey(Item.id))
    file_id=Column(Integer, ForeignKey("files.id"))
    object_name=Column(String)
    object_description=Column(String)
    object_description_raw=Column(String)

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
    

class ItemRelationship(Base, core_mixin):

    __tablename__="itemrelationship"

    id=Column(Integer, primary_key=True)
    parent_id=Column(Integer, ForeignKey(Item.id))
    child_id=Column(Integer, ForeignKey(Item.id))
    quantity=Column(Integer)

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