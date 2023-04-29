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
