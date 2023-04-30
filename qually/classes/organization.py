from qually.helpers.class_imports import *

class Organization(Base, core_mixin):

    __tablename__="organizations"

    #basic info
    id = Column(Integer, primary_key=True)
    name = Column(String, default=None)
    license_count = Column(Integer, default=0)
    license_expire_utc = Column(Integer, default=0)

    created_utc = Column(Integer, default=0)
    creation_ip = Column(String, default=None)

    #organization settings
    requires_otp = Column(Boolean, default=False)

    #Organization record counters
    ncmr_counter = Column(Integer, default=0)
    capa_counter = Column(Integer, default=0)
    dev_counter = Column(Integer, default=0)
    
    sop_counter = Column(Integer, default=0)
    wi_counter = Column(Integer, default=0)

    tp_counter = Column(Integer, default=0)
    tr_counter = Column(Integer, default=0)

    co_counter = Column(Integer, default=0)

    #Organization staffmin settings
    is_banned=Column(Boolean, default=False)

    logs=relationship("OrganizationAuditLog", lazy="dynamic")

class OrganizationAuditLog(Base, core_mixin):

    __tablename__="organization_log"

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    creation_ip=Column(String(128))
    user_id=Column(Integer, ForeignKey("users.id"))
    organization_id=Column(Integer, ForeignKey("organizations.id"))

    key=Column(String)
    old_value=Column(String)
    new_value=Column(String)
    note=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)

    def __init__(self, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"] = g.timestamp

        if "creation_ip" not in kwargs:
            kwargs["creation_ip"] = request.remote_addr

        if g.user and ("user_id" not in kwargs):
            kwargs["user_id"] = g.user.id

        if g.user and ("organization_id" not in kwargs):
            kwargs["organization_id"] = g.user.organization_id

        Base.__init__(self, **kwargs)

    @property
    def permalink(self):
        return f"/settings/audit/{self.base36id}"
    