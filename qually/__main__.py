import gevent.monkey
gevent.monkey.patch_all()

from os import environ, path
import time
from secrets import token_hex
from redis import BlockingConnectionPool, ConnectionPool
import sass

from flask import g, session, Flask, request, redirect
from flask_caching import Cache
from flask_limiter import Limiter

from flaskext.markdown import Markdown

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import *
from sqlalchemy.orm import Session, sessionmaker, scoped_session, joinedload
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

from werkzeug.middleware.proxy_fix import ProxyFix


_version = "0.0.1"

app = Flask(__name__,
            template_folder='./templates'
            )

app.config["PROXYFIX_X_FOR"]=int(environ.get("PROXYFIX", "2").lstrip().rstrip())
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config["PROXYFIX_X_FOR"])
app.url_map.strict_slashes = False

#Site name and branding
app.config["SITE_NAME"]=environ.get("SITE_NAME", "Qually").lstrip().rstrip()
app.config["TAGLINE"]=environ.get("TAGLINE", "Alpha").lstrip().rstrip()
app.config["SUBTITLE"]=environ.get("SUBTITLE", "").lstrip().rstrip()

#Colors - default to bootstrap defaults
app.config['COLOR_PRIMARY']=environ.get("COLOR_PRIMARY",'0d6efd')
app.config['COLOR_SECONDARY']=environ.get("COLOR_SECONDARY",'6c757d')
app.config['CSS_URL']=f"/assets/style/{app.config['COLOR_PRIMARY']}/{app.config['COLOR_SECONDARY']}.css"

app.config["SYSPATH"]=environ.get("SYSPATH", path.dirname(path.realpath(__file__)))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATABASE_URL'] = environ.get("DATABASE_URL","").replace("postgres://", "postgresql://")

app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
app.config["ADMIN_EMAIL"]=environ.get("ADMIN_EMAIL","").lstrip().rstrip()

app.config["SERVER_NAME"] = environ.get("SERVER_NAME", environ.get("domain", f"{app.config['SITE_NAME'].lower()}.herokuapp.com")).lstrip().rstrip() 


app.config["HTTPS"] = int(environ.get("HTTPS", 1)) or not any([x in app.config["SERVER_NAME"] for x in ["localhost","127.0.0.1"]])
app.config["DISABLE_SIGNUPS"]=int(environ.get("DISABLE_SIGNUPS",0))

# Cookie stuff
app.config["SESSION_COOKIE_NAME"] = f"__Host-{app.config['SERVER_NAME']}"
app.config["VERSION"] = _version
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"] = app.config["HTTPS"]
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_DOMAIN"] = False
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 365
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

#Mailgun
app.config["MAILGUN_KEY"]=environ.get("MAILGUN_KEY")

app.jinja_env.cache = {}

app.config["UserAgent"] = f"Content Aquisition for {app.config['SERVER_NAME']} v{_version}."

if not environ.get("REDIS_URL"):
    app.config["CACHE_TYPE"] = "FileSystemCache"
else:
    app.config["CACHE_TYPE"] = environ.get("CACHE_TYPE", 'NullCache').lstrip().rstrip()

app.config["CACHE_DIR"] = environ.get("CACHE_DIR", "tempcache")

# Redis configs
app.config["CACHE_REDIS_URL"] = environ.get("REDIS_URL","").rstrip().lstrip()
app.config["CACHE_DEFAULT_TIMEOUT"] = 60
app.config["CACHE_KEY_PREFIX"] = "flask_caching_"
app.config["REDIS_POOL_SIZE"]=int(environ.get("REDIS_POOL_SIZE", 3))

# AWS configs
app.config["S3_BUCKET"]=environ.get("S3_BUCKET","").lstrip().rstrip()
app.config["AWS_ACCESS_KEY_ID"]=environ.get("AWS_ACCESS_KEY_ID","").lstrip().rstrip()
app.config["AWS_SECRET_ACCESS_ID"]=environ.get("AWS_SECRET_ACCESS_ID","").lstrip().rstrip()

redispool=ConnectionPool(
    max_connections=app.config["REDIS_POOL_SIZE"],
    host=app.config["CACHE_REDIS_URL"].split("://")[1]
    ) if app.config["CACHE_TYPE"]=="redis" else None
app.config["CACHE_OPTIONS"]={'connection_pool':redispool} if app.config["CACHE_TYPE"]=="redis" else {}

app.config["READ_ONLY"]=bool(int(environ.get("READ_ONLY", False)))

app.config["DEBUG"]=bool(int(environ.get("DEBUG", 0)))

#precompute logo urls
# app.config["IMG_URL_LOGO_WHITE"] = f"/logo/white/{app.config['COLOR_PRIMARY'].lower()}/{app.config['SITE_NAME'][0].lower()}"
# app.config["IMG_URL_LOGO_MAIN"] = f"/logo/main/{app.config['COLOR_PRIMARY'].lower()}/{app.config['SITE_NAME'][0].lower()}"
# app.config["IMG_URL_JUMBOTRON"] = f"/logo/jumbotron/{app.config['COLOR_PRIMARY'].lower()}/{app.config['SITE_NAME'][0].lower()}"
# app.config["IMG_URL_FAVICON"]=f"/logo/splash/{app.config['COLOR_PRIMARY']}/{app.config['SITE_NAME'][0].lower()}/64/64"
# app.config["IMG_URL_THUMBSPLASH"]=f"/logo/splash/{app.config['COLOR_PRIMARY']}/{app.config['SITE_NAME'][0].lower()}/1200/630"

#Cloudflare Turnstile
app.config["CLOUDFLARE_TURNSTILE_KEY"]=environ.get("CLOUDFLARE_TURNSTILE_KEY",'').lstrip().rstrip()
app.config["CLOUDFLARE_TURNSTILE_SECRET"]=environ.get("CLOUDFLARE_TURNSTILE_SECRET",'').lstrip().rstrip()

Markdown(app)
cache = Cache(app)

# app.config["CACHE_REDIS_URL"]
app.config["RATELIMIT_STORAGE_URI"] = environ.get("REDIS_URL", 'memory://').lstrip().rstrip()
app.config["RATELIMIT_KEY_PREFIX"] = "flask_limiting_"
app.config["RATELIMIT_ENABLED"] = not bool(int(environ.get("DISABLE_RATELIMIT", 0)))
app.config["RATELIMIT_DEFAULTS_DEDUCT_WHEN"]=lambda x:True
app.config["RATELIMIT_DEFAULTS_EXEMPT_WHEN"]=lambda:False
app.config["RATELIMIT_HEADERS_ENABLED"]=True

#Business variables
app.config["CENTS_PER_SEATYEAR"]=int(environ.get("CENTS_PER_SEATYEAR", 10000))

limiter = Limiter(
    key_func = lambda: request.remote_addr,
    app=app,
    application_limits=["60/minute"],
    headers_enabled=True,
    strategy="fixed-window",
    storage_uri=app.config["RATELIMIT_STORAGE_URI"]#,
    #on_breach=ban_ip
)

_engine=create_engine(
    app.config['DATABASE_URL'],
    poolclass=QueuePool,
    pool_size=int(environ.get("PG_POOL_SIZE",5)),
    pool_use_lifo=True
)

db_session=scoped_session(sessionmaker(bind=_engine))

Base = declarative_base()

#debug function

def debug(text):
    if app.config["DEBUG"]:
        print(text)

# import and bind all classes, routes, and template filters functions
from qually.helpers.security import generate_hash
import qually.classes
from qually.routes import *
import qually.helpers.jinja2
from qually.helpers.get import *
from qually.helpers.security import generate_hash, validate_hash

#purge css from cache
#cache.delete_memoized(qually.routes.main_css)

# enforce https
@app.before_request
def before_request():

    #Force SSL
    if app.config["HTTPS"] and request.url.startswith(
            "http://") and "localhost" not in app.config["SERVER_NAME"]:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url), 301
    
    #cookie stuff
    session.permanent = True
    if "session_id" not in session:
        session["session_id"] = token_hex(16)

    #request values
    g.time = int(time.time())
    g.nonce=generate_hash(f'{g.time}+{session.get("session_id")}')
    g.db = db_session()

    #default user to none
    g.user=None

    #Check for authentication
    if session.get("user_id"):
        user = g.db.query(User).options(joinedload(User.organization)).filter_by(id=session.get("user_id")).first()
        if user and user.is_active and user.login_nonce == session.get("login_nonce", 0):
            g.user = user
        else:
            session.pop("user_id")
            session.pop("login_nonce")

    #for non-idempotent requests, check csrf token
    if request.method in ["POST", "PUT", "PATCH", "DELETE"] and request.url_rule:

        submitted_key = request.values.get("csrf_token")

        if not submitted_key:
            abort(403)

        if g.user:
            if not g.user.validate_csrf_token(submitted_key):
                abort(403)
        
        else:
            t=int(request.values.get("time",0))
            if g.time - t > 3600:
                abort(403)
            if not validate_hash(f"{t}+{session['session_id']}", submitted_key):
                abort(403)

    if g.user and g.user.reset_pw_next_login and not request.path.startswith(("/set_password", "/help/", "/assets", "/logout")):
        return redirect("/set_password")

    if g.user and g.user.organization.requires_otp and not g.user.otp_secret and not request.path.startswith(("/set_otp","/help/","/assets/","/logout")):
        return redirect("/set_otp")



@app.after_request
def after_request(response):

    try:
        debug([g.get('user'), request.method, request.path, request.url_rule])
    except:
        debug(["<detached>", request.method, request.path, request.url_rule])

        
    response.headers.add('Access-Control-Allow-Headers',
                         "Origin, X-Requested-With, Content-Type, Accept, x-auth")
    response.headers.add("Strict-Transport-Security", "max-age=31536000")
    response.headers.add("Referrer-Policy", "same-origin")
    response.headers.add("X-Content-Type-Options","nosniff")
    response.headers.add("Permissions-Policy",
        "geolocation=(), midi=(), notifications=(), push=(), sync-xhr=(), microphone=(), camera=(), magnetometer=(), gyroscope=(), vibrate=(), payment=()")

    if app.config["HTTPS"]:
        response.headers.add("Content-Security-Policy", 
            f"default-src https:; form-action {app.config['SERVER_NAME']}; frame-src {app.config['SERVER_NAME']}  challenges.cloudflare.com *.hcaptcha.com *.youtube.com youtube.com platform.twitter.com; object-src none; style-src 'self' 'nonce-{g.nonce}' maxcdn.bootstrapcdn.com unpkg.com cdn.jsdelivr.net; script-src 'self' 'nonce-{g.nonce}' challenges.cloudflare.com *.hcaptcha.com hcaptcha.com code.jquery.com cdnjs.cloudflare.com stackpath.bootstrapcdn.com cdn.jsdelivr.net unpkg.com platform.twitter.com; img-src https: data:")


    if not request.path.startswith(("/assets/js/", "/assets/css/", "/logo/")):
        response.headers.add("X-Frame-Options", "deny")

    return response

@app.teardown_request
def teardown_request(resp):

    try:
        g.db.close()
    except:
        pass

    return True


@app.route("/<path:path>", subdomain="www")
def www_redirect(path):

    return redirect(f"https://{app.config['SERVER_NAME']}/{path}")
