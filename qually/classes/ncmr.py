from qually.helpers.class_imports import *
_=T

class NCMR(Base, core_mixin):

    __tablename__="ncmr"

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    number=Column(Integer, default=0, index=True)
    _status = Column(Integer, default=0)

    ##relationships
    organization=relationship("Organization")
    owner = relationship("User")
    logs = relationship("NCMRLog", order_by="NCMRLog.id.desc()")

    ##process data
    item_number=Column(String)
    lot_number=Column(String)
    quantity=Column(String)
    nc_description=Column(String)
    nc_description_raw=Column(String)


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
        return _("NCMR-")+f"{self.number:0>5}"

    @property
    def _lifecycle(self):
        return {
            0: _("New"),
            1: _("Submitted"),
            2: _("Material Review Board"),
            3: _("Disposition"),
            4: _("Closed"),
            100: _("Terminated")
        }
    

    @property
    def status(self):

        return self._lifecycle[self._status]

    @property
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
                }
            ]
        }
    
    

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