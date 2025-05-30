from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x

class NCMR(Base, core_mixin, process_mixin):

    __tablename__="ncmr"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    number=Column(Integer, default=0, index=True)
    _status = Column(Integer, default=0)

    _name="NCMR"

    __table_args__=(
            UniqueConstraint(
                'number', 
                'organization_id',
                name=f'ncmr_org_number_unique'
                ),
            )

    organization=relationship("Organization")

    @classmethod
    def name_readable(cls):
        return _("Non-Conforming Material Report")

    @classmethod
    def _assignment_query_args(cls):

        args= [
            and_(
                NCMR._status==0, 
                NCMR.owner_id==g.user.id
                ),
            and_(
                NCMR._status==3,
                NCMR.assignee_id==g.user.id
                )
            ]

        if g.user.is_doc_control:
            args.append(NCMR._status.in_([1,4]))
        
        if g.user.is_mrb:
            args.append(NCMR._status==2)

        return args

    @property
    def _lifecycle(self):
        return {
            0: {
                'name': _("New"),
                'users': [self.owner],
                'files': True
                },
            1: {
                'name': _("Initial Review"),
                'users': self.organization.doc_control_users
                },
            2: {
                'name': _("Material Review Board"),
                'users': self.organization.mrb_users
                },
            3: {
                'name': _("Disposition"),
                'users': [self.assignee],
                'files': True
                },
            4: {
                'name': _("Final Review"),
                'users': self.organization.doc_control_users
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
    @org_lang
    def _dispositions(cls):

        return {
                    1: _("Scrap"),
                    2: _("Return to Supplier"),
                    3: _("Rework"),
                    4: _("Use As-Is"),
                    5: _("Reclassify")
            }

    @classmethod
    def _layout(cls):
        return {
            0:[
                {
                    "name":_("Item Number"),
                    "value":"item_number",
                    "kind": "text"
                },
                {
                    "name":_("Revision Number"),
                    "value":"revision",
                    "kind": "text"
                },
                {
                    "name":_("Serial or Lot Number"),
                    "value":"lot_number",
                    "kind": "text"
                },
                {
                    "name":_("Quantity"),
                    "value":"quantity",
                    "kind": "text"
                },
                {
                    "name":_("Description of Non-Conformance"),
                    "value":"nc_description",
                    "kind": "multi",
                    "help":_("Identify the specification or requirement to which the material fails to conform.")
                },
                {
                    "name":_("Additional Comments"),
                    "value":"new_comments",
                    "kind": "multi"
                }
            ],
            1:[],
            2:[
                {
                    "name":_("Assigned Disposition"),
                    "value":"_disposition_determined",
                    "kind": "dropdown",
                    "values": cls._dispositions()
                },
                {
                    "name":_("Material Review Board Comments"),
                    "value":"mrb_comments",
                    "kind": "multi"
                },
                {
                    "name":_("Disposition Assignee"),
                    "value":"assignee",
                    "kind": "user"
                }

            ],
            3:[
                {
                    "name":_("Executed Disposition"),
                    "value":"_disposition_actual",
                    "kind": "dropdown",
                    "values": cls._dispositions()
                },
                {
                    "name":_("Additional Comments"),
                    "value":"dsp_comments",
                    "kind": "multi"
                }
            ],
            4: []
        }
    
    @property
    @lazy
    def _transitions(self):

        return {
            0: [
                {
                    "id":"submit",
                    "to": 1,
                    "name": _("Submit"),
                    "description": _("Submit this record to Document Control for review."),
                    "color": "success",
                    "users": [self.owner],
                    "approval":True
                },
                {
                    "id":"terminate",
                    "to": 101,
                    "name": _("Terminate"),
                    "description": _("Permanently archive this record. This cannot be undone."),
                    "color": "danger",
                    "users": [self.owner]
                }
            ],
            1: [
                {
                    "id":"reject",
                    "to": 0,
                    "name": _("Reject"),
                    "description": _("Send this record back to its initiator for revision."),
                    "users": g.user.organization.doc_control_users,
                    "color": "secondary",
                    "comments": True,
                },
                {
                    "id":"withdraw",
                    "to": 0,
                    "name": _("Withdraw"),
                    "users": [self.owner],
                    "color": "secondary"
                },
                {
                    "id":"advance",
                    "to": 2,
                    "name": _("Advance"),
                    "description": _("Send this record to the Material Review Board."),
                    "users": g.user.organization.doc_control_users,
                    "color": "success",
                    "approval":True
                },
                {
                    "id":"terminate",
                    "to": 101,
                    "name": _("Terminate"),
                    "description": _("Permanently archive this record. This cannot be undone."),
                    "users": g.user.organization.doc_control_users,
                    "color": "danger"
                }
            ],
            2: [
                {
                    "id":"approve",
                    "to":3,
                    "name": _("Approve"),
                    "description": _("Approve of the planned disposition."),
                    "users": g.user.organization.mrb_users,
                    "color": "success",
                    "approval":True
                },
            ],
            3: [
                {
                    "id":"return",
                    "to":2,
                    "name": _("Return to Material Review Board"),
                    "description": _("Return to Material Review Board."),
                    "users": g.user.organization.doc_control_users,
                    "color": "secondary"
                },
                {
                    "id":"submit",
                    "to":4,
                    "name": _("Submit"),
                    "description": _("Submit for final review."),
                    "users": [self.assignee],
                    "color": "success",
                    "approval":True
                }
            ],
            4: [
                {
                    "id":"reject-mrb",
                    "to":2,
                    "name": _("Reject to MRB"),
                    "description": _("Reject back to the Material Review Board."),
                    "users": g.user.organization.doc_control_users,
                    "color": "warning"
                },
                {
                    "id":"reject-dsp",
                    "to":3,
                    "name": _("Reject to  Disposition"),
                    "description": _("Reject back to the Disposition assignee."),
                    "users": g.user.organization.doc_control_users,
                    "color": "warning"
                },
                {
                    "id":"close",
                    "to":100,
                    "name": _("Close"),
                    "description": _("Approve and close this record."),
                    "users": g.user.organization.doc_control_users,
                    "color": "success",
                    "approval":True
                }
            ]
        }

NCMR._cols()
    
class NCMRApproval(Base, core_mixin):

    __tablename__="ncmr_approval"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("ncmr.id"), index=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    status_id=Column(Integer)
    created_utc=Column(Integer)
    user_name=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)


class NCMRLog(Base, core_mixin):

    __tablename__="ncmr_audit"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("ncmr.id"), index=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    created_ip=Column(String(64))

    key=Column(String)
    value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)

class NCMRView(Base, core_mixin):

    __tablename__="ncmr_view"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("ncmr.id"), index=True)
    user_id=Column(Integer, ForeignKey("users.id"), index=True)
    created_utc=Column(BigInteger)

    record=relationship("NCMR", lazy="joined", innerjoin=True)
    user=relationship("User", lazy="joined", innerjoin=True)
    __table_args__=(
        UniqueConstraint(
            'record_id', 
            'user_id',
            name=f'ncmr_view_user_unique'
            ),
        )   

NCMR._view_class=NCMRView