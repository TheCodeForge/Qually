from flask import *
from sqlalchemy import *
from sqlalchemy.orm import *

from .mixins import core_mixin

from qually.__main__ import Base, cache, app, g, db_session, debug

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
    is_mfa_required = Column(Boolean, default=False)
