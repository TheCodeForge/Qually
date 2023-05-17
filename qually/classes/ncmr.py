from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _, force_locale
except ModuleNotFoundError:
    pass

class NCMR(Base, core_mixin):

    __tablename__="ncmr"

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"))
    number=Column(Integer, default=0, index=True)
    _status = Column(Integer, default=0)

    ##relationships
    organization=relationship("Organization")
    owner = relationship("User", primaryjoin="User.id==NCMR.owner_id")
    assignee = relationship("User", primaryjoin="User.id==NCMR.assignee_id")
    logs = relationship("NCMRLog", order_by="NCMRLog.id.desc()")
    approvals=relationship("NCMRApproval")

    ##New
    item_number=Column(String, default="")
    lot_number=Column(String, default="")
    quantity=Column(String, default="")
    nc_description=Column(String, default="")
    nc_description_raw=Column(String, default="")
    new_comments=Column(String, default="")
    new_comments_raw =Column(String, default="")

    ##MRB
    _disposition_determined=Column(Integer, default=None)
    mrb_comments=Column(String, default="")
    mrb_comments_raw =Column(String, default="")

    ##MRB
    _disposition_actual=Column(Integer, default=None)
    dsp_comments=Column(String, default="")
    dsp_comments_raw =Column(String, default="")


    __table_args__=(
        UniqueConstraint(
            'number', 
            'organization_id', name='ncmr_org_number_unique'),
        )



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
                'users': self.organization.doc_control_users
                },
            2: {
                'name': _("Material Review Board"),
                'users': self.organization.mrb_users,
                },
            3: {
                'name': _("Disposition"),
                'users': [self.assignee]
                },
            4: {
                'name': _("Final Review"),
                'users': self.organization.doc_control_users
                },
            5: {
                'name': _("Closed"),
                'users': []
                },
            100: {
                'name': _("Terminated"),
                'users': []
                }
        }

    @property
    def _dispositions(self):

        with force_locale(g.user.organization.lang):
            return {
                0: _("Scrap"),
                1: _("Return to Supplier"),
                2: _("Rework"),
                3: _("Use As-Is"),
                4: _("Reclassify")
            }
    
    

    @property
    def status(self):

        return self._lifecycle[self._status]['name']

    @property
    @lazy
    def _layout(self):
        return {
            0:[
                {
                "name":_("Item Number"),
                "value":"item_number",
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
                "raw": "nc_description_raw"
                },
                {
                "name":_("Additional Comments"),
                "value":"new_comments",
                "kind": "multi",
                "raw": "new_comments_raw"
                }
            ],
            2:[
                {
                "name":_("Assigned Disposition"),
                "value":"_disposition_determined",
                "kind": "dropdown",
                "values": self._dispositions
                },
                {
                "name":_("Material Review Board Comments"),
                "value":"mrb_comments",
                "kind": "multi",
                "raw": "mrb_comments_raw"
                }
            ],
            3:[
                {
                "name":_("Executed Disposition"),
                "value":"_disposition_actual",
                "kind": "dropdown",
                "values": self._dispositions
                },
                {
                "name":_("Additional Comments"),
                "value":"dsp_comments",
                "kind": "multi",
                "raw": "dsp_comments_raw"
                }
            ]
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
                    "users": [self.owner]
                },
                {
                    "id":"terminate",
                    "to": 100,
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
                    "description": _("Send this record back to its initiator for revision"),
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
                    "description": _("Send this record to the Material Review Board"),
                    "users": g.user.organization.doc_control_users,
                    "color": "success"
                },
                {
                    "id":"terminate",
                    "to": 100,
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
                }
            ],
            3: [
                {
                    "id":"submit",
                    "to":4,
                    "name": _("Submit"),
                    "description": _("Submit for final review."),
                    "users": [self.assignee],
                    "color": "success"
                }
            ],
            4: [
                {
                    "id":"reject-mrb",
                    "to":2,
                    "name": _("Reject to Material Review Board"),
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
                    "to":5,
                    "name": _("Close"),
                    "description": _("Approve and close this record."),
                    "users": g.user.organization.doc_control_users,
                    "color": "success"
                }
            ]
        }
    
class NCMRApproval(Base, core_mixin):

    __tablename__="ncmr_approval"

    id = Column(Integer, primary_key=True)
    ncmr_id=Column(Integer, ForeignKey("ncmr.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    status_id=Column(Integer)
    created_utc=Column(Integer)

    user=relationship("User", lazy="joined", innerjoin=True)


class NCMRLog(Base, core_mixin):

    __tablename__="ncmr_audit"

    id = Column(Integer, primary_key=True)
    ncmr_id=Column(Integer, ForeignKey("ncmr.id"))
    user_id=Column(Integer, ForeignKey("users.id"))
    created_utc=Column(Integer)
    created_ip=Column(String(64))

    key=Column(String)
    value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)