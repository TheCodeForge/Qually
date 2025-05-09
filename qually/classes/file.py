from qually.helpers.class_imports import *

class File(Base, core_mixin):

    __tablename__="files"

    id=Column(Integer)

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    organization_id = Column(Integer, ForeignKey("organizations.id"), index=True)
    creator_id=Column(Integer, ForeignKey("users.id"))
    sha512=Column(String(128))
    status_id=Column(Integer)
    file_name=Column(String)

    #connection IDs
    ncmr_id = Column(Integer, ForeignKey("ncmr.id"),            index=True)
    capa_id = Column(Integer, ForeignKey("capa.id"),            index=True)
    dvtn_id = Column(Integer, ForeignKey("dvtn.id"),            index=True)
    rvsn_id = Column(Integer, ForeignKey("itemrevision.id"),    index=True)
    chng_id = Column(Integer, ForeignKey("chng.id"),            index=True)

    ncmr=           relationship("NCMR",            lazy="joined", backref="files")
    capa=           relationship("CAPA",            lazy="joined", backref="files")
    deviation=      relationship("Deviation",       lazy="joined", backref="files")
    itemrevision=   relationship("ItemRevision",    lazy="joined", backref="files")
    change=         relationship("ChangeOrder",     lazy="joined", backref="_files")

    stage_id=Column(Integer)

    #relationships
    organization=relationship("Organization", lazy="joined", viewonly=True)
    creator=relationship("User", lazy="joined")

    @property
    def s3_name(self):
        return f"organization/{self.organization.base36id}/file/{self.base36id}/{self.file_name}"

    @property
    def s3_link(self):
        return f"/s3/{self.s3_name}"

    @property
    def owning_object(self):
        return self.ncmr or self.capa or self.deviation or self.itemrevision or self.change