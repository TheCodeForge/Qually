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

    revisions=relationship("ItemRevision", lazy="dynamic", order_by="ItemRevision.id.desc()", viewonly=True)

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

        return g.user.organization.next_id(cls._kinds()[int(request.form.get('_kind_id'))]['orgname'])

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

        data[0] =[
            {
                "name": _("Type"),
                "value":"_kind_id",
                "kind": "dropdown",
                "values": {x:cls._kinds()[x]['name'] for x in cls._kinds()},
                "hide": lambda self: True
            },
            {
                "name": _("Custom Number"),
                "value":"custom_number",
                "kind": "text",
                "placeholder": _("Leave blank to set item number automatically."),
                "hide": lambda self: True
            }
        ]+data[0]

        return data

    @property
    @lazy
    def proposed_revision(self):
        return self.revisions.filter_by(_status=0).first()

    @property
    @lazy
    def current_revision(self):
        return self.revisions.filter_by(_status=1).first()

    @property
    @lazy
    def display_revision(self):
        if self._status<=1:
            return self.proposed_revision
        else:
            return self.current_revision

    @property
    def name(self):
        return self.custom_number or f"{getattr(g.user.organization, f'{self.kind.lower()}_prefix')}-{self.number:0>5}"

    def _after_create(self):

        ir = ItemRevision(
            item_id=self.id,
            created_utc=g.time,
            object_name=txt(request.form.get("object_name")),
            object_description=txt(request.form.get("object_description")),
            object_description_raw=html(request.form.get("object_description")),
            _status=0
            )
        self._status=0
        g.db.add(ir)
        g.db.add(self)
        g.db.commit()
    
    def _edit_form(self):

        if self._status==0:
            return self.proposed_revision._edit_form()

        elif self._status==1:

            self.proposed_revision._status=2

            ir = ItemRevision(
                item_id=self.id,
                created_utc=g.time,
                _status=0,
                revision_number = self.current_revision+1
                )

            g.db.add(ir)
            g.db.add(self.proposed_revision)
            results = ir._edit_form()
            g.db.flush()
            return results

        else:
            return toast_error("Can't edit that right now")

class ItemRevision(Base, core_mixin, process_mixin):

    __tablename__="itemrevision"

    id=Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    item_id=Column(Integer, ForeignKey(Item.id))
    file_id=Column(Integer, ForeignKey("files.id"))
    object_name=Column(String, default="")
    object_description=Column(String, default="")
    object_description_raw=Column(String, default="")
    revision_number=Column(Integer, default=0)

    _status=Column(Integer, default=0)

    item=relationship("Item", lazy="joined", viewonly=True)

    __table_args__=(
        UniqueConstraint(
            'item_id', 
            'revision_number',
            name=f'item_rev_number_unique'
            ),
        )   


    @property
    def _lifecycle(self):
        return {
            0:{
                'name':_("Proposed"),
                'users': [g.user],
            },
            1:{
                'name':_("Effective"),
                'users': []
            },
            2:{
                'name':_("Superceded"),
                'users':[]
            }
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