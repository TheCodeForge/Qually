from qually.helpers.class_imports import *
from .user import User
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    def _(x):
        return x

class Organization(Base, core_mixin, process_mixin):

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
    part_prefix = Column(String(5), default="PART")
    chng_prefix = Column(String(5), default="CHNG")
    sop_prefix = Column(String(5), default="SOP")
    wi_prefix = Column(String(5), default="WI")
    

    #Organization record counters
    ncmr_counter = Column(Integer, default=0)
    capa_counter = Column(Integer, default=0)
    dvtn_counter = Column(Integer, default=0)
    chng_counter = Column(Integer, default=0)

    part_counter = Column(Integer, default=0)    
    sop_counter = Column(Integer, default=0)
    wi_counter = Column(Integer, default=0)

    # tp_counter = Column(Integer, default=0)
    # tr_counter = Column(Integer, default=0)

    #Organization staffmin settings
    is_banned=Column(Boolean, default=False)

    #relationships
    _users=relationship("User", lazy="dynamic")
    logs=relationship("OrganizationAuditLog", lazy="dynamic", order_by="OrganizationAuditLog.id.desc()")
    approver_groups=relationship(
        "ChangeApproverGroup", 
        lazy="dynamic", 
        primaryjoin="ChangeApproverGroup.organization_id==Organization.id and ChangeApproverGroup.is_active==True", 
        viewonly=True, 
        order_by="ChangeApproverGroup.id.asc()"
        )
    
    ncmrs=relationship("NCMR",      lazy="dynamic", viewonly=True)
    capas=relationship("CAPA",      lazy="dynamic", viewonly=True)
    dvtns=relationship("Deviation", lazy="dynamic", viewonly=True)
    items=relationship("Item",      lazy="dynamic", viewonly=True)
    chngs=relationship("ChangeOrder", lazy="dynamic", viewonly=True)
    parts=relationship("Item",      lazy="dynamic", viewonly=True, primaryjoin="Item.organization_id==Organization.id and Item._kind_id==1")
    sops =relationship("Item",      lazy="dynamic", viewonly=True, primaryjoin="Item.organization_id==Organization.id and Item._kind_id==2")
    wis  =relationship("Item",      lazy="dynamic", viewonly=True, primaryjoin="Item.organization_id==Organization.id and Item._kind_id==3")
    files=relationship("File",      lazy="dynamic", viewonly=True)

    _status=0

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

    def get_record(self, prefix, number, rev=None, graceful=False):

        for kind in ['ncmr', 'capa', 'dvtn', 'chng', 'part', 'sop', 'wi']:
            if getattr(self, f"{kind.lower()}_prefix").lower()==prefix.lower():
                break

        else:
            if graceful:
                return None
            else:
                abort(404)

        record= getattr(self, f"{kind.lower()}s").filter_by(number=int(number)).first()

        if not record:
            if graceful:
                return None
            else:
                abort(404)

        if rev:
            record.__dict__['display_revision']=record.revisions.filter_by(revision_number=int(rev)).first()

        record.modify_layout()

        return record

    def next_id(self, kind):
        setattr(self, f"{kind}_counter", 1+getattr(self, f"{kind}_counter"))
        g.db.add(self)
        g.db.commit()
        return getattr(self, f"{kind}_counter")
    

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

    @property
    def _lifecycle(self):

        return {
            0: {
                'name': _("Branding"),
                'users': [g.user] if g.user.is_org_admin else [],
                'early':'edit' 
            },
            1: {
                'name': _("Security"),
                'users': [g.user] if g.user.is_org_admin else [],
                'early':'edit' 
            },
            2: {
                'name': _("Localization"),
                'users': [g.user] if g.user.is_org_admin else [],
                'early':'edit' 
            },
            3: {
                'name': _("Prefixes"),
                'users': [g.user] if g.user.is_org_admin else [],
                'early':'edit' 
            }
        }

        # return {
        #     0:{
        #         'name': _("Prefixes"),
        #         'users': [g.user] if g.user.is_org_admin else [],
        #         'hide_title':True,
        #         'early':'edit'
        #     }
        # }

    @classmethod
    def _layout(self):
        return {
            0:[
                {
                    'name': _("Organization Name"),
                    'kind':'text',
                    'value': 'name'
                },
                {
                    'name': _("Color"),
                    'kind': 'text',
                    'value': 'color'
                }
            ],
            1:[
                {
                    'name': _("Require Two-Factor Authentication"),
                    'kind': 'dropdown',
                    'value': 'requires_otp',
                    'values': {
                        0:_("No"),
                        1:_("Yes")
                    },
                    'validate': lambda x: bool(g.user.otp_secret) or not int(request.form.get("requires_otp")),
                    'validate_fail_msg': _("You must have two-factor authentication enabled on your own account first.")
                }
            ],
            2:[
                {
                    'name': _("Default Language"),
                    'kind':'dropdown',
                    'value': 'lang',
                    'values': {LANGUAGES[x]:x for x in LANGUAGES},
                    'help': _("Sets the language for new users and audit logs.")
                },
                {
                    'name': _("Default Time Zone"),
                    'kind': 'dropdown',
                    'value': 'tz',
                    'values': {x:x for x in TIMEZONES},
                    'help': _("Sets the default time zone for new users.")
                }
            ],
            3:[
                {
                    'name':_("Corrective and Preventive Action"),
                    'value':'capa_prefix',
                    'kind':"text"
                },
                {
                    'name':_("Change Order"),
                    'value':'chng_prefix',
                    'kind':"text"
                },
                {
                    'name':_("Deviation"),
                    'value':'dvtn_prefix',
                    'kind':"text"
                },
                {
                    'name':_("Non-Conforming Material Report"),
                    'value':'ncmr_prefix',
                    'kind':"text"
                },
                {
                    'name':_("Part"),
                    'value':'part_prefix',
                    'kind':"text"
                },
                {
                    'name':_("Standard Operating Procedure"),
                    'value':'sop_prefix',
                    'kind':"text"
                },
                {
                    'name':_("Work Instruction"),
                    'value':'wi_prefix',
                    'kind':"text"
                }
            ]
        }
    
    
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
    