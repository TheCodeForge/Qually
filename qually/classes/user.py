from secrets import token_hex
import pyotp

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
    referred_by = Column(Integer, default=None)
    is_active = Column(Boolean, default=True)
    has_license = Column(Boolean, default=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))

    #security
    login_nonce = Column(Integer, default=0)
    otp_secret = deferred(Column(String(64), default=None))

    #profile
    has_profile = Column(Boolean, default=False)
    profile_nonce = Column(Integer, default=0)

    ## === RELATIONSHIPS ===

    organization = relationship("Organization", lazy="joined", innerjoin=True)

    __table_args__=(
        Index(
            "users_email_trgm_idx", "email",
            postgresql_using="gin",
            postgresql_ops={
                'email':'gin_trgm_ops'
                }
            ),
        )

    def __init__(self, **kwargs):

        if "password" in kwargs:

            kwargs["passhash"] = self.hash_password(kwargs["password"])
            kwargs.pop("password")

        if "created_utc" not in kwargs:
            kwargs["created_utc"] = g.timestamp

        super().__init__(**kwargs)


    def __repr__(self):
        return f"<User(username={self.username}, org={self.organization.name})>"

    def validate_2fa(self, token):

        x = pyotp.TOTP(self.mfa_secret)
        return x.verify(token, valid_window=1)

    def validate_csrf_token(self, token):

        return validate_hash(f"{session['session_id']}+{self.id}+{self.login_nonce}", token)

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
        return f"/@{self.username}"

    def set_profile(self, file):

        self.del_profile()
        self.profile_nonce += 1

        aws.upload_file(name=f"uid/{self.base36id}/profile-{self.profile_nonce}.png",
                        file=file,
                        resize=(100, 100)
                        )
        self.has_profile = True
        self.profile_upload_ip=request.remote_addr
        self.profile_set_utc=g.timestamp
        self.profile_upload_region=request.headers.get("cf-ipcountry")
        g.db.add(self)
        g.db.commit()

    def del_profile(self, db=None):

        aws.delete_file(name=f"uid/{self.base36id}/profile-{self.profile_nonce}.png")
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

        if self.has_profile and not self.is_deleted:
            return f"https://{app.config['S3_BUCKET']}/uid/{self.base36id}/profile-{self.profile_nonce}.png"
        else:
            return f"http{'s' if app.config['FORCE_HTTPS'] else ''}://{app.config['SERVER_NAME']}/logo/fontawesome/solid//{app.config['COLOR_PRIMARY']}/150"

    @property
    def json_core(self):
        data= {
            'name': self.name,
            'permalink': self.permalink,
            'created_utc': self.created_utc,
            'id': self.base36id,
            'is_private': self.is_private,
            'profile_url': self.profile_url,
            'banner_url': self.banner_url,
            'title': self.title.json if self.title else None,
            'bio': self.bio,
            'bio_html': self.bio_html
            }

        return data
    
    @property
    def json(self):
        return self.json_core
    
    @property
    def txn_history(self):
        return self._transactions.filter(PayPalTxn.status!=1).order_by(PayPalTxn.created_utc.desc()).all()
