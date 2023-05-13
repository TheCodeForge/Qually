from qually.helpers.class_imports import *

class NCMR(Base):

    __tablename__="ncmr"

    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    number=Column(Integer, default=0)
    _status = Column(Integer, default=0)

    ##relationships
    organization=relationship("Organization")
    owner = relationship("User")

    ##process data
    item_number=Column(String)
    lot_number=Column(String)
    qty=Column(Float)


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
        return f"NCMR-{self.number:0>5}"

    @property
    def status(self):
        lifecycle = [
            "Open",
            "Submitted",
            "Material Review Board",
            "Disposition",
            "Closed"
            ]
        return lifecycle[self._status]
