from qually.helpers.class_imports import *
from .user import User

class Organization(Base, core_mixin):

    __tablename__="organizations"

    #basic info
    id = Column(Integer, primary_key=True)
    name = Column(String, default=None)

    #licensing data
    license_count = Column(Integer, default=0)
    license_expire_utc = Column(BigInteger, default=0)
    licenses_last_increased_utc=Column(Integer, default=0)

    created_utc = Column(Integer, default=0)
    creation_ip = Column(String, default=None)

    #organization settings
    requires_otp = Column(Boolean, default=False)
    lang = Column(String(2), default="en")
    tz = Column(String, default="UTC")
    color=Column(String(6), default=app.config['COLOR_PRIMARY'])

    #Prefix settings
    ncmr_prefix = Column(String(5), default="NCMR")
    capa_prefix = Column(String(5), default="CAPA")
    dvtn_prefix = Column(String(5), default="DVTN")

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

    #relationships
    _users=relationship("User", lazy="dynamic")
    logs=relationship("OrganizationAuditLog", lazy="dynamic", order_by="OrganizationAuditLog.id.desc()")
    
    ncmrs=relationship("NCMR",       lazy="dynamic", viewonly=True)
    capas=relationship("CAPA",       lazy="dynamic", viewonly=True)
    dvtns=relationship("Deviation",  lazy="dynamic", viewonly=True)

    @classmethod
    def _cols(cls):


        def wrapper(value):

            @property
            @lazy
            def wrapped(self):

                kwargs={
                    'is_active':True,
                    value: True
                    }

                return list(self._users.filter_by(**kwargs).all())

            return wrapped

        for role in ROLES:
            setattr(cls, role['rel'], wrapper(role['value']))


    def __init__(self, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"] = g.time

        if "creation_ip" not in kwargs:
            kwargs["creation_ip"] = request.remote_addr

        super().__init__(**kwargs)

    def get_record(self, prefix, number):

        for kind in ['ncmr', 'capa', 'dvtn']:
            if getattr(self, f"{kind}_prefix").lower()==prefix.lower():
                break

        else:
            abort(404)

        record= getattr(self, f"{kind}s").filter_by(number=int(number)).first()
        if not record:
            abort(404)

        return record

    @property
    def next_ncmr_id(self):
        self.ncmr_counter+=1
        g.db.add(self)
        g.db.commit()
        return self.ncmr_counter


    @property
    def next_capa_id(self):
        self.capa_counter+=1
        g.db.add(self)
        g.db.commit()
        return self.capa_counter


    @property
    def next_dvtn_id(self):
        self.capa_counter+=1
        g.db.add(self)
        g.db.commit()
        return self.capa_counter

    @property
    @lazy
    def licenses_used(self):
        return self.users.filter_by(has_license=True).count()
    
    @property
    @lazy
    def users(self):
        if g.user.is_org_admin:
            return self._users.order_by(User.name.asc())
        else:
            return self._users.filter_by(is_active=True).order_by(User.name.asc())

    @property
    @lazy
    def assignable_users(self):
        return self._users.filter_by(is_active=True, has_license=True).order_by(User.name.asc())
    

    @property
    @lazy
    def license_expire_date(self):
        return time.strftime("%d %B %Y", time.gmtime(self.license_expire_utc))
    
Organization._cols()
    

class OrganizationAuditLog(Base, core_mixin):

    __tablename__="organization_log"

    id = Column(Integer, primary_key=True)
    created_utc=Column(Integer)
    creation_ip=Column(String(128))
    user_id=Column(Integer, ForeignKey("users.id"))
    organization_id=Column(Integer, ForeignKey("organizations.id"))

    key=Column(String)
    new_value=Column(String)

    user=relationship("User", lazy="joined", innerjoin=True)

    def __init__(self, **kwargs):

        if "created_utc" not in kwargs:
            kwargs["created_utc"] = g.time

        if "creation_ip" not in kwargs:
            kwargs["creation_ip"] = request.remote_addr

        if "user_id" not in kwargs:
            kwargs["user_id"]=g.user.id

        if "organization_id" not in kwargs:
            kwargs["organization_id"]=g.user.organization.id

        super().__init__(**kwargs)

    @property
    def permalink(self):
        return f"/settings/audit/{self.base36id}"
    