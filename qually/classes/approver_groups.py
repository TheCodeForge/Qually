from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x


class ChangeApproverGroup(Base, core_mixin, process_mixin):

    __tablename__="chng_approver_group"

    id=Column(Integer, primary_key=True)

    organization_id=Column(Integer, ForeignKey("organizations.id"))
    name=Column(String(128), nullable=False)
    requires_all=Column(Boolean, default=True, nullable=False)

    user_relationships=relationship("ChangeApproverGroupRelationship")
    organization=relationship("Organization", viewonly=True)
    _status=0

    @property
    def users(self):
        return [x.user for x in self.user_relationships]

    @property
    def permalink(self):
        return f"/settings/approvers/{self.base36id}"

    @property
    def _lifecycle(self):

        return {
            0:{
                'name': self.name,
                'users': g.user.organization.doc_control_users,
                'hide_title':True
            }
        }

    @classmethod
    def _layout(cls):

        return {
            0:[
                {
                    "name":_("Group Name"),
                    "value":"name",
                    "kind": "text"
                },
                {
                    "name":_("Mode"),
                    "value":"requires_all",
                    "kind":"dropdown",
                    "help":_("Set the number of approvals required, when this approval group is assigned."),
                    "values": {
                        0:_("One Required"),
                        1:_("All Required")
                    }
                },
                {
                    "name":_("Group Members"),
                    "value":"user_relationships",
                    "kind":"user_multi"
                }
            ]
        }
    

class ChangeApproverGroupRelationship(Base):

    __tablename__="chnge_approver_group_relationship"

    id=Column(Integer, primary_key=True)

    record_id=Column(Integer, ForeignKey("chng_approver_group.id"), nullable=False)
    user_id=Column(Integer, ForeignKey("users.id"), nullable=False)

    user=relationship("User")

    __table_args__=(
        UniqueConstraint(
            'record_id', 
            'user_id',
            name=f'approver_group_rel_grp_user_unique'
            ),
        )


ChangeApproverGroup._user_relationships_obj = ChangeApproverGroupRelationship