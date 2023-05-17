from secrets import token_hex
import pyotp
from hmac import compare_digest

from qually.helpers.security import otp_recovery_code
from qually.helpers.class_imports import *

class User(Base, core_mixin):

    __tablename__ = "users"

    #basic stuff
    id = Column(Integer, primary_key=True)
    email = Column(String, default=None)
    passhash = deferred(Column(String, default=None))
    created_utc = Column(Integer, default=0)
    creation_ip = Column(String, default=None)
    name = Column(String, default=None)
    is_active = Column(Boolean, default=True)
    has_license = Column(Boolean, default=False)
    license_assigned_utc=Column(Integer, default=0)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    is_org_admin = Column(Boolean, default=False)

    #security
    login_nonce = Column(Integer, default=0)
    otp_secret = deferred(Column(String(64), default=None))
    reset_pw_next_login = Column(Boolean, default=False)
    last_otp_code = Column(Integer, default=0)

    #profile
    has_profile = Column(Boolean, default=False)
    profile_nonce = Column(Integer, default=0)
    profile_upload_ip=deferred(Column(String(255), default=None))
    profile_upload_region=deferred(Column(String(2)))
    title = Column(String, default="")
    lang = Column(String(2), default="en")
    tz = Column(String, default="UTC")

    #business roles
    is_doc_control=Column(Boolean, default=False)
    is_mrb=Column(Boolean, default=False)

    ## === RELATIONSHIPS ===

    organization = relationship("Organization", lazy="joined", innerjoin=True, viewonly=True)

    __table_args__=(
        Index(
            "users_email_trgm_idx", "email",
            postgresql_using="gin",
            postgresql_ops={
                'email':'gin_trgm_ops'
                }
            ),
        UniqueConstraint(
            'email', 
            'organization_id', name='_email_org_unique')
        )

    def __init__(self, **kwargs):

        if "password" in kwargs:

            kwargs["passhash"] = self.hash_password(kwargs["password"])
            kwargs.pop("password")

        if "created_utc" not in kwargs:
            kwargs["created_utc"] = g.time

        super().__init__(**kwargs)


    def __repr__(self):
        return f"<User(id={self.base36id})>"

    def __str__(self):
        return f"{self.name} <{self.email}>"

    def validate_otp(self, x, allow_reset=False):

        if not self.otp_secret:
            return True

        if x==self.last_otp_code:
            return False
            
        totp=pyotp.TOTP(self.otp_secret)
        if totp.verify(x, valid_window=1):
            self.last_otp_code=x
            g.db.add(self)
            g.db.commit()
            return True
        elif allow_reset and compare_digest(x.replace(' ','').upper(), otp_recovery_code(self, self.otp_secret)):
            self.otp_secret==None
            self.last_otp_code=None
            g.db.add(self)
            g.db.commit()
            return True
        return False

    def validate_csrf_token(self, token):

        return validate_hash(f"{session['session_id']}+{self.id}+{self.login_nonce}", token)

    @property
    def has_seat(self):
        return self.has_license and self.organization.license_expire_utc>g.time

    @property
    def mfa_removal_code(self):

        hashstr = f"{self.mfa_secret}+{self.id}+{self.original_username}"

        hashstr= generate_hash(hashstr)

        removal_code = base36encode(int(hashstr,16) % int('z'*25, 36))

        #should be 25char long, left pad if needed
        while len(removal_code)<25:
            removal_code="0"+removal_code

        return removal_code

    @property
    def csrf_token(self):

        msg = f"{session['session_id']}+{self.id}+{self.login_nonce}"

        return generate_hash(msg)

    @property
    @lazy
    def permalink(self):
        return f"/user/{self.base36id}"

    def set_profile(self, file):

        self.del_profile()
        self.profile_nonce += 1

        aws.upload_file(name=f"user/{self.base36id}/profile-{self.profile_nonce}.png",
                        file=file,
                        resize=(100, 100)
                        )
        self.has_profile = True
        self.profile_upload_ip=request.remote_addr
        self.profile_upload_region=request.headers.get("cf-ipcountry")
        g.db.add(self)
        g.db.commit()

    def del_profile(self, db=None):

        aws.delete_file(name=f"user/{self.base36id}/profile-{self.profile_nonce}.png")
        self.has_profile = False
        self.profile_nonce+=1
        if db:
            db.add(self)
            db.commit()
            db.close()
        else:
            g.db.add(self)
            g.db.commit()    

    @property
    def profile_url(self):

        if self.has_profile:
            return f"/s3/user/{self.base36id}/profile-{self.profile_nonce}.png"
        else:
            return f"/icon/fontawesome/solid//{app.config['COLOR_PRIMARY']}/100"

    @property
    def json_core(self):
        data= {
            'name': self.name,
            'permalink': self.permalink,
            'created_utc': self.created_utc,
            'id': self.base36id,
            'is_private': self.is_private,
            'profile_url': self.profile_url,
            'bio': self.bio,
            'bio_html': self.bio_html
            }

        return data
    
    @property
    def json(self):
        return self.json_core

    @property
    def role_string(self):
        
        roles=[]
        if self.is_org_admin:
            roles.append(_("Administrator"))

        return ', '.join(roles)
    