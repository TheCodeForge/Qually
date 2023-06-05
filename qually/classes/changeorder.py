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
                }
            ]
        }

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