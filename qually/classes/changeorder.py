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
        return self.__dict__.get("_lifecycle") or {
            0: {
                'name': _("New"),
                'users': [self.owner],
                'title_text':_("Summary")
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
            ],
            96:[
                # {
                #     "name":_("Impact Assessors"),
                #     "value":"impact_assessor",
                #     "kind":"user"
                # }
            ]
        }

    def modify_layout(self):

        #Modify display based on attached items

        layout = self.__class__._layout()
        lifecycle = self._lifecycle

        if self._status==0 and self.can_edit(0):
            layout[1]=[
                {
                    "name":_("Add Item"),
                    "value":"add_item",
                    "kind":"text",
                    "hide":lambda x:len(self.proposed_revisions)>=90
                },
                {
                    "name":_("Remove Item"),
                    "value":"delete_item",
                    "kind":"dropdown",
                    "values":{
                        x.base36id:x.item.name for x in self.proposed_revisions
                    },
                    "hide":lambda x:len(self.proposed_revisions)==0
                }
            ]
            lifecycle[1]={
                'name': _("Add/Remove Items"),
                'users': [self.owner],
                'early':'edit'
            }

        i=2

        for rev in self.proposed_revisions:
            layout[i]= rev._layout()[0]
            lifecycle[i]={
                'name':rev.item.name,
                'users': [g.user],
                'files':True,
                'early':'edit',
                'object_data': rev,
                'title_link': rev.item.permalink
            }
            i+=1

        self.__dict__["_layout"]=lambda:layout
        self.__dict__['_lifecycle']=lifecycle

        print(self._layout())
        print(self._lifecycle)

    @property
    def files(self):
        output=[]
        for rev in self.proposed_revisions:
            for f in rev.files:
                output.append(f)

        return output
    

    @property
    @lazy
    def _transitions(self):
        return {
            0: [
                {
                    "id":"submit",
                    "to": 96,
                    "name": _("Submit"),
                    "description": _("Submit this record to Document Control for review."),
                    "color": "success",
                    "users": [g.user],
                    "approval":True
                },
                {
                    "id":"terminate",
                    "to": 101,
                    "name": _("Terminate"),
                    "description": _("Permanently archive this record. This cannot be undone."),
                    "color": "danger",
                    "users": [self.owner]+g.user.organization.doc_control_users
                }
            ],
            96: [
                {
                    "id":"reject",
                    "to": 0,
                    "name": _("Reject"),
                    "description": _("Return this record to the Summary phase."),
                    "color": "warning",
                    "users": g.user.organization.doc_control_users
                },
                {
                    "id":"withdraw",
                    "to": 0,
                    "name": _("Withdraw"),
                    "description": _("Return this record to the Summary phase."),
                    "color": "warning",
                    "users": [self.owner]
                }
            ]
        }

    def _edit_form(self):

        special_handling=["add_item", "delete_item", "add_assessor", "delete_assessor", "add_approver","delete_approver"]
        for x in special_handling:
            if request.form.get(x):
                break
        else:
            return process_mixin._edit_form(self)

        if x=="add_item":

            name=request.form.get("add_item")

            if self._status>0:
                return toast_error(_("This record has changed status. Please reload this page."), 409)

            try:
                prefix, number=name.split('-')
            except:
                return toast_error(_("Invalid item number"), 400)

            item=g.user.organization.items.filter_by(number=int(number)).first()

            if not item:
                return toast_error(_("No item found with number {x}").format(x=name), 404)

            if item.id in [x.item_id for x in self.proposed_revisions]:
                return toast_error(_("Item {x} is already associated with this change").format(x=item.name), 409)

            new_ir = item.new_revision()

            new_ir.change_id=self.id
            g.db.add(new_ir)
            g.db.commit()

            return _("Add Item"), item.name, "", True

        elif x=="delete_item":

            if self._status>0:
                return toast_error(_("This record has changed status. Please reload this page."), 409)

            rev=[x for x in self.proposed_revisions if x.id==int(request.form.get("delete_item"), 36)][0]

            name=rev.item.name

            for file in rev.files:
                aws.delete_file(file.s3_name)
                g.db.delete(file)
            g.db.delete(rev)
            g.db.commit()

            return  _("Remove Item"), name, "", True


    def _after_phase_change(self):

        if self._status!=100:
            return

        for rev in self.proposed_revisions:

            #supersede current revisions
            existing=rev.item.effective_revision
            existing._status=2
            g.db.add(existing)

            rev._status=1
            g.db.add(rev)

        g.db.commit()


ChangeOrder._cols()

class ChangeOrderAssessorRelationship(Base, core_mixin):

    __tablename__="chng_assessor_relationship"

    id=Column(Integer, primary_key=True)
    change_id=Column(Integer, ForeignKey('chng.id'))
    user_id=Column(Integer, ForeignKey('users.id'))

    change=relationship("ChangeOrder", backref="assessor_relationships")
    user=relationship("User", backref="change_assessor_relationships")

class ChangeOrderApproverRelationship(Base, core_mixin):

    __tablename__="chng_approver_relationship"

    id=Column(Integer, primary_key=True)
    change_id=Column(Integer, ForeignKey('chng.id'))
    user_id=Column(Integer, ForeignKey('users.id'))

    change=relationship("ChangeOrder", backref="approver_relationships")
    user=relationship("User", backref="change_approver_relationships")

    
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