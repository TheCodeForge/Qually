from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x


class Item(Base, core_mixin, revisioned_process_mixin):

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
            UniqueConstraint(
                'custom_number',
                'organization_id',
                name=f'item_org_custom_number_unique'
                )
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
                "placeholder": _("Assign a custom number to this item."),
                "hide": lambda self: not bool(self.custom_number)
            }
        ]+data[0]

        return data

    @property
    def name(self):

        if self.custom_number:
            return self.custom_number

        prefix_id=self._kinds()[self._kind_id]['orgname'].lower()
        prefix=getattr(g.user.organization, f"{prefix_id}_prefix")
        return f"{prefix}-{self.number:0>5}"

    def _after_create(self):

        ir = ItemRevision(
            item_id=self.id,
            created_utc=g.time,
            object_name=txt(request.form.get("object_name")),
            object_description=html(request.form.get("object_description")),
            object_description_raw=txt(request.form.get("object_description")),
            _status=1
            )
        self._status=0
        g.db.add(ir)
        g.db.add(self)
        g.db.commit()
    
    def _edit_form(self):

        checks= process_mixin._edit_form(self)
        if checks[0]:
            return checks

        if self._status==0:
            return self.effective_revision._edit_form()

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

    @property
    def object_name(self):
        return self.effective_revision.object_name

    @object_name.setter
    def object_name(self, value):
        if self._status==0:
            self.effective_revision.object_name = value

    @property
    def object_description(self):
        return self.effective_revision.object_description

    @object_description.setter
    def object_description(self, value):
        if self._status==0:
            self.effective_revision.object_description = value

    @property
    def object_description_raw(self):
        return self.effective_revision.object_description_raw

    @object_description_raw.setter
    def object_description_raw(self, value):
        if self._status==0:
            self.effective_revision.object_description_raw = value


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
                'users': [g.user] if self.item._status==0 else []
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