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