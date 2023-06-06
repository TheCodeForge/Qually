from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x


class ChangeOrder(Base, core_mixin, process_mixin):

    __tablename__="chng"
    id=Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    number=Column(Integer, default=0, index=True)
    _status = Column(Integer, default=0)

    _name="CHNG"

    __table_args__=(
            UniqueConstraint(
                'number', 
                'organization_id',
                name=f'chng_org_number_unique'
                ),
            )

    organization=relationship("Organization")

    @classmethod
    def name_readable(cls):
        return _("Change Order")

    @property
    def _lifecycle(self):
        return {
            0: {
                'name': _("New"),
                'users': [self.owner]
                },
            1: {
                'name': _("Initial Review"),
                'users': self.organization.doc_control_users
                },
            2: {
                'name': _("Approvals"),
                'users': []
                },
            98: {
                'name': _("Implementation"),
                'users': [self.owner],
                'files': True
                },
            99: {
                'name': _("Approval of Implementation"),
                'users': self.organization.quality_mgmt_users
                },
            100: {
                'name': _("Closed"),
                'users': []
                },
            101: {
                'name': _("Terminated"),
                'users': []
                }
        }

    @classmethod
    def _layout(cls):
        data= {
            0:[
                {
                    "name":_("Name"),
                    "value":"record_name",
                    "kind": "text"
                },
                {
                    "name":_("Description of Changes"),
                    "value":"change_description",
                    "kind": "multi"
                },
                {
                    "name":_("Rationale for Changes"),
                    "value":"change_rationale",
                    "kind": "multi"
                }
            ]
        }

        if not request.path.startswith("/create_"):
            data[0].append(
                {
                    "name":_("Add Item"),
                    "value":"add_item",
                    "kind":"text",
                    "column":False
                }
            )

        return data

    @property
    @lazy
    def _transitions(self):
        return {
            0: [
                # {
                #     "id":"submit",
                #     "to": 1,
                #     "name": _("Submit"),
                #     "description": _("Submit this record to Document Control for review."),
                #     "color": "success",
                #     "users": [self.owner],
                #     "approval":True
                # },
                {
                    "id":"terminate",
                    "to": 101,
                    "name": _("Terminate"),
                    "description": _("Permanently archive this record. This cannot be undone."),
                    "color": "danger",
                    "users": [self.owner]+g.user.organization.doc_control_users
                }
            ]
        }

    def _edit_form(self):

        if not request.form.get("add_item"):
            return process_mixin._edit_form(self)

        name=request.form.get("add_item")
        
        try:
            prefix, number=name.split('-')
        except:
            return toast_error(_("Invalid item number"), 400)

        item=g.user.organization.get_record(prefix, number)

        if not item:
            return toast_error(_("No item found with number {x}").format(x=name), 400)

        new_ir = ItemRevision(
            item_id=item.id,
            change_id=self.id,
            object_name=item.object_name,
            object_description=item.object_description,
            object_description_raw=item.object_description_raw
            )

        g.db.add(new_ir)

        g.db.commit()

        return _("Add Item"), item.name, "", True



ChangeOrder._cols()
    
class ChangeOrderApproval(Base, core_mixin):

    __tablename__="chng_approval"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("chng.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    status_id=Column(Integer)
    created_utc=Column(Integer)

    user=relationship("User", lazy="joined", innerjoin=True)


class ChangeOrderLog(Base, core_mixin):

    __tablename__="chng_audit"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("chng.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    created_ip=Column(String(64))

    key=Column(String)
    value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)