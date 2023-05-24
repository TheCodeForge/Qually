from qually.helpers.class_imports import *

class File(Base, core_mixin):

    __tablename__="files"

    id=Column(Integer)

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    created_by=Column(Integer, ForeignKey("users.id"))
    sha_256=Column(String(512))

    #relationships
    organization=relationship("Organization", lazy="joined")
    creator=relationship("User", lazy="joined")


    @property
    def s3_link(self):

        return f"/s3/organization/{self.organization.base36id}/file/{self.base36id}"
    