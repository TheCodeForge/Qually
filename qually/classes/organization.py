from flask import g, session, abort, request
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey, FetchedValue, Index, and_, or_, select, func
from sqlalchemy.orm import relationship, deferred, joinedload, lazyload, contains_eager, aliased, Load, load_only

from .mixins import core_mixin

from qually.__main__ import Base, cache, app, g, db_session, debug

class Organization(Base, core_mixin):

    __tablename__="organizations"

    id = Column(Integer, primary_key=True)
    name = Column(String, default=None)
    license_count = Column(Integer, default=0)

    created_utc = Column(Integer, default=0)
    creation_ip = Column(String, default=None)

