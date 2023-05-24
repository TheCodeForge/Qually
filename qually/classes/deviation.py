from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _, force_locale
except ModuleNotFoundError:
    def _(x):
        return x

class Deviation(Base, core_mixin, process_mixin):

    __tablename__="ncmr"

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    number=Column(Integer, default=0, index=True)
    _status = Column(Integer, default=0)

    _name="DVTN"

    __table_args__=(
            UniqueConstraint(
                'number', 
                'organization_id',
                name=f'ncmr_org_number_unique'
                ),
            )

    organization=relationship("Organization")

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

        if g.user.is_quality_management:
            args.append(NCMR._status.in_([1,4]))
        
        if g.user.is_mrb:
            args.append(NCMR._status==2)

        return args

    @property
    def permalink(self):
        return f"/NCMR-{self.number:0>5}"
    
    @property
    def name(self):
        with force_locale(g.user.organization.lang):
            return _("NCMR-")+f"{self.number:0>5}"

    @property
    def _lifecycle(self):
        return {
            0: {
                'name': _("New"),
                'users': [self.owner]
                },
            1: {
                'name': _("Initial Review"),
                'users': self.organization.quality_mgmt_users
                },
            2: {
                'name': _("Corrections"),
                'users': self.organization.mrb_users
                },
            3: {
                'name': _("Final Review"),
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
    def _plan_types(cls):

        data=lambda:{
                    0: _("Planned"),
                    1: _("Unplanned")
            }

        try:
            with force_locale(g.user.organization.lang):
                return data()
        except (RuntimeError, NameError) as e:
            return data()

    @classmethod
    def _layout(cls):
        return {
            0:[
                {
                    "name":_("Description of deviation"),
                    "value":"dvtn_description",
                    "kind": "multi",
                    "help":_("Identify the process or procedure not being followed.")
                },
                {
                    "name":_("Planned?"),
                    "value":"is_unplanned",
                    "kind": "dropdown",
                    "values": cls._plan_types(),
                },
                {
                    "name":_("Immediate Corrections"),
                    "value":"initial_corrections",
                    "kind": "multi",
                    "values": cls._plan_types(),
                    "help": _("Describe initial corrections performed, if any.")
                }
            ],
            1:[
                {
                    "name":_("Further corrections"),
                    "value": "outstanding_corrections",
                    "kind": "multi",
                    "help": "Identify outstanding corrections needed, if any."
                },
                {
                    "name":_("Corrections Assignee"),
                    "value": "corrections_assignee",
                    "kind": "user",
                    "help": _("Identify individual responsible for completing further corrections.")
                }
            ],
            2:[
                {
                    "name":_("Final corrections"),
                    "value":"final_corrections",
                    "kind": "multi",
                    "help": _("Record corrective actions performed.")
                }

            ],
            3:[]
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
                    "users": g.user.organization.quality_mgmt_users,
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
                    "description": _("Advance this record to Corrections."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "success",
                    "approval":True
                },
                {
                    "id":"approve_and_close",
                    "to": 100,
                    "name": _("Close - No Further Corrections"),
                    "description": _("Approve and close this record with no further corrections needed."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "success"
                },
                {
                    "id":"terminate",
                    "to": 101,
                    "name": _("Terminate"),
                    "description": _("Permanently archive this record. This cannot be undone."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "danger"
                }
            ],
            2: [
                {
                    "id":"submit",
                    "to":3,
                    "name": _("Submit"),
                    "description": _("Submit for final review."),
                    "users": [self.corrections_assignee],
                    "color": "success",
                    "approval":True
                },
            ],
            3: [
                {
                    "id":"return",
                    "to":2,
                    "name": _("Return to Corrections"),
                    "description": _("Return to Corrections."),
                    "users": g.user.organization.quality_mgmt_users,
                    "color": "secondary"
                },
                {
                    "id":"close",
                    "to":100,
                    "name": _("Approve and Close"),
                    "description": _("Submit for final review."),
                    "users": g.user.organization.quality_mgmt_users,
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
    
class DeviationApproval(Base, core_mixin):

    __tablename__="ncmr_approval"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("ncmr.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    status_id=Column(Integer)
    created_utc=Column(Integer)

    user=relationship("User", lazy="joined", innerjoin=True)


class DeviationLog(Base, core_mixin):

    __tablename__="ncmr_audit"

    id = Column(Integer, primary_key=True)
    record_id=Column(Integer, ForeignKey("ncmr.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    created_ip=Column(String(64))

    key=Column(String)
    value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)