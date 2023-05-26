from qually.helpers.class_imports import *

class File(Base, core_mixin):

    __tablename__="files"

    id=Column(Integer)

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    creator_id=Column(Integer, ForeignKey("users.id"))
    sha512=Column(String(128))
    file_name=Column(String)

    #connection IDs
    ncmr_id = Column(Integer, ForeignKey("ncmr.id"))
    capa_id = Column(Integer, ForeignKey("capa.id"))
    dvtn_id = Column(Integer, ForeignKey("dvtn.id"))

    ncmr=relationship("NCMR", lazy="joined", backref="files")
    capa=relationship("CAPA", lazy="joined", backref="files")
    deviation=relationship("Deviation", lazy="joined", backref="files")

    stage_id=Column(Integer)

    #relationships
    organization=relationship("Organization", lazy="joined")
    creator=relationship("User", lazy="joined")

    @property
    def s3_name(self):
        return f"/organization/{self.organization.base36id}/file/{self.base36id}"

    @property
    def s3_link(self):
        return f"/s3{self.s3_name}"
    

    @property
    def owning_object(self):
        return self.ncmr or self.capa
    
    