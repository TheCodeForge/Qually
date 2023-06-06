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

    proposed_revisions=relationship("ItemRevision", order_by="ItemRevision.id.asc()", viewonly=True)

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
            96: {
                'name': _("Initial Review"),
                'users': self.organization.doc_control_users
                },
            97: {
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
        return {
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

    def modify_layout(self):

        #Modify display based on attached items

        layout = self.__class__._layout()
        lifecycle = self._lifecycle

        if self._status==0 and self.can_edit(0):
            layout[0].append(
                {
                    "name":_("Add Item"),
                    "value":"add_item",
                    "kind":"text"
                }
            )

        i=1

        for rev in self.proposed_revisions:
            layout[i]= rev._layout()[0]
            lifecycle[i]={
                'name':rev.item.name,
                'users': [g.user],
                'files':True,
                'early':'edit'
            }

        self.__dict__["_layout"]=lambda:layout
        self.__dict__["_lifecycle"]=lifecycle

        print("layout")
        print(self._layout())
        print("lifecycle")
        print(self._lifecycle)

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

        item=g.user.organization.get_record(prefix, number, graceful=True)

        if not item:
            return toast_error(_("No item found with number {x}").format(x=name), 400)

        new_ir = item._revision_class(
            item_id=item.id,
            change_id=self.id,
            object_name=item.object_name,
            object_description=item.object_description,
            object_description_raw=item.object_description_raw,
            created_utc=g.time
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