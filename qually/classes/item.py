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
    custom_number=Column(String, default=None)

    logs=relationship("ItemLog", order_by="ItemLog.id.desc()")
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
        return self.__dict__.get("_lifecycle") or {
            0: {
                'name': _("Draft"),
                'users': [self.owner],
                'files': True,
                'hide_title':True
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
                },
            101: {
                'name': _("Abandoned"),
                'users': []
                }
        }

    @property
    def _transitions(self):
        return {
            0: [
                {
                    "id":"abandon",
                    "to": 101,
                    "name": _("Abandon"),
                    "description": _("Abandon this record. You may recover it later if you wish."),
                    "color": "danger",
                    "users": [self.owner]
                }
            ],
            101: [
                {
                    "id":"abandon",
                    "to": 0,
                    "name": _("Restore"),
                    "description": _("Restore this record to the draft state."),
                    "color": "success",
                    "users": [self.owner]
                }
            ]
        }

    @classmethod
    @org_lang
    def _layout(cls):
        data = cls._revision_class._layout()

        data[0] =[
            {
                "name": _("Type"),
                "value":"_kind_id",
                "kind": "dropdown",
                "values": {x:cls._kinds()[x]['name'] for x in cls._kinds()},
                "hide": lambda x:True
            # },
            # {
            #     "name": _("Custom Number"),
            #     "value":"custom_number",
            #     "kind": "text",
            #     "placeholder": _("Assign a custom number to this item."),
            #     "hide": lambda self: not bool(self.item.custom_number) #phase 0 is ItemRev object
            }
        ]+data[0]

        return data

    def modify_layout(self):
        #Override this to customize the record display based on custom data
        layout=self._layout()
        lifecycle=self._lifecycle

        lifecycle[0]={
            'name': _("Draft"),
            'users': [g.user],
            'files': True,
            'title_text': self.display_revision.status,
            'object_data':self.display_revision,
            'files_label':_("Item Files"),
            'ignore_file_section':True
        }

        self.__dict__["_layout"]=lambda:layout
        self.__dict__["_lifecycle"]=lifecycle

        #At the same time, adjust _lifecycle as follows
        # @property
        # def _lifecycle(self)
        #     return self.__dict__.get("_lifecycle") or {.....}
        pass

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
    

    @property
    def files(self):
        return self.display_revision.files

    def new_revision(self):

        new_ir = self._revision_class(
            item_id=self.id,
            object_name=self.effective_revision.object_name,
            object_description=self.effective_revision.object_description,
            object_description_raw=self.effective_revision.object_description_raw,
            created_utc=g.time,
            revision_item_lifecycle_to=self._status or 2
            )
        g.db.add(new_ir)
        g.db.flush()

        for file_obj in self.effective_revision.files:
            new_file_obj=file_obj.__class__(
                created_utc=g.time,
                organization_id=g.user.organization.id,
                rvsn_id=new_ir.id,
                file_name=file_obj.file_name,
                status_id=file_obj.status_id,
                creator_id=g.user.id,
                stage_id=file_obj.stage_id
                )
            g.db.add(new_file_obj)
            g.db.flush()

            f, mime = aws.download_file(file_obj.s3_name)
            aws.upload_buffer(new_file_obj.s3_name, f)

        g.db.commit()

        return new_ir    


class ItemRevision(Base, core_mixin, process_mixin):

    __tablename__="itemrevision"

    id=Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    item_id=Column(Integer, ForeignKey(Item.id), index=True)
    object_name=Column(String, default="")
    object_description=Column(String, default="")
    object_description_raw=Column(String, default="")
    revision_number=Column(Integer, default=None)
    revision_item_lifecycle_to=Column(Integer, default=None)

    _status=Column(Integer, default=0)
    status_utc=Column(BigInteger, default=None)

    change_id = Column(Integer, ForeignKey("chng.id"))

    item=relationship("Item", lazy="joined", viewonly=True)
    change=relationship("ChangeOrder")

    __table_args__=(
        UniqueConstraint(
            'item_id', 
            'revision_number',
            name=f'item_rev_number_unique'
            ),
        UniqueConstraint(
            'item_id', 
            'change_id',
            name=f'item_change_unique'
            )
        )   

    @property
    def name(self):
        return self.item.name

    @property
    def permalink(self):
        return f"{self.item.permalink}/revision/{self.revision_number}"
    

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
            },
            3:{
                'name':_("Expired"),
                'users':[]
            }
        }

    @property
    def status(self):
        return self._lifecycle[self._status]['name']

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
                    "name": _("Revision"),
                    "value":"revision_number",
                    "kind": "int",
                    "hide": lambda x:x.revision_number in [None,0],
                    "readonly":True
                },
                {
                    "name": _("Status"),
                    "value": "revision_item_lifecycle_to",
                    "kind":"dropdown",
                    "values":{
                        2: _("Production"),
                        100: _("Obsolete")
                    },
                    "hide": lambda x: request.path == x.item.permalink
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
    parent_id=Column(Integer, ForeignKey(Item.id), index=True)
    child_id=Column(Integer, ForeignKey(Item.id), index=True)
    quantity=Column(Integer)

class ItemLog(Base, core_mixin):

    __tablename__="item_audit"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("item.id"), index=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    created_ip=Column(String(64))

    key=Column(String)
    value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)

class ItemView(Base, core_mixin):

    __tablename__="item_view"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("item.id"), index=True)
    user_id=Column(Integer, ForeignKey("users.id"), index=True)
    created_utc=Column(BigInteger)

    record=relationship("Item", lazy="joined", innerjoin=True)
    user=relationship("User", lazy="joined", innerjoin=True)
    __table_args__=(
        UniqueConstraint(
            'record_id', 
            'user_id',
            name=f'item_view_user_unique'
            ),
        )   

Item._revision_class=ItemRevision
Item._view_class=ItemView