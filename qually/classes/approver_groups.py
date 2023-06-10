from qually.helpers.class_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x


class ChangeApproverGroup(Base, core_mixin):

    __tablename__="chng_approver_group"

    id=Column(Integer, primary_key=True)

    organization_id=Column(Integer, ForeignKey("organizations.id"))
    name=Column(String(128), nullable=False)

    user_relationships=relationship("ChangeApproverGroupRelationship")
    organization=relationship("Organization", viewonly=True)

    @property
    def users(self):
        return [x.user for x in self.user_relationships]

    @property
    def permalink(self):
        return f"/settings/approvers/{self.base36id}"
    

class ChangeApproverGroupRelationship(Base):

    __tablename__="chnge_approver_group_relationship"

    id=Column(Integer, primary_key=True)

    group_id=Column(Integer, ForeignKey("chng_approver_group.id"))
    user_id=Column(Integer, ForeignKey("users.id"))

    user=relationship("User")
