import gevent.monkey
gevent.monkey.patch_all()

from os import environ, path
from secrets import token_hex
from flask import Flask, redirect, render_template, jsonify, abort, g, request
from flask_caching import Cache
from flask_limiter import Limiter
from flask_minify import Minify
from collections import deque
from psycopg2.errors import UndefinedColumn
from sys import getsizeof

from flaskext.markdown import Markdown
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError, StatementError, InternalError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
#import threading
#import random
from redis import Redis

from redis import BlockingConnectionPool, ConnectionPool

from werkzeug.middleware.proxy_fix import ProxyFix


_version = "0.0.1"

app = Flask(__name__,
            template_folder='./templates'
            )

app.config["PROXYFIX_X_FOR"]=int(environ.get("PROXYFIX", "2").lstrip().rstrip())
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=app.config["PROXYFIX_X_FOR"])
app.url_map.strict_slashes = False

app.config["SITE_NAME"]=environ.get("SITE_NAME", "Qually").lstrip().rstrip()
app.config["TAGLINE"]=environ.get("TAGLINE", "Alpha").lstrip().rstrip()
app.config["SUBTITLE"]=environ.get("SUBTITLE", "").lstrip().rstrip()

app.config["SYSPATH"]=environ.get("SYSPATH", path.dirname(path.realpath(__file__)))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DATABASE_URL'] = environ.get("DATABASE_URL","").replace("postgres://", "postgresql://")

app.config['SECRET_KEY'] = environ.get('SECRET_KEY')
app.config["ADMIN_EMAIL"]=environ.get("ADMIN_EMAIL","").lstrip().rstrip()

app.config["SERVER_NAME"] = environ.get("SERVER_NAME", environ.get("domain", f"{app.config['SITE_NAME'].lower()}.herokuapp.com")).lstrip().rstrip() 

# Cookie stuff
app.config["SESSION_COOKIE_NAME"] = f"__Host-{app.config['SERVER_NAME']}"
app.config["VERSION"] = _version
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.config["SESSION_COOKIE_SECURE"] = bool(int(environ.get("FORCE_HTTPS", 1)))
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_DOMAIN"] = False

app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 365
app.config["SESSION_REFRESH_EACH_REQUEST"] = True

app.config["FORCE_HTTPS"] = int(environ.get("FORCE_HTTPS", 1)) if not any([x in app.config["SERVER_NAME"] for x in ["localhost","127.0.0.1"]]) else 0
app.config["DISABLE_SIGNUPS"]=int(environ.get("DISABLE_SIGNUPS",0))

app.jinja_env.cache = {}

app.config["UserAgent"] = f"Content Aquisition for {app.config['SERVER_NAME']} v{_version}."

if not environ.get("REDIS_URL"):
    app.config["CACHE_TYPE"] = "FileSystemCache"
else:
    app.config["CACHE_TYPE"] = environ.get("CACHE_TYPE", 'NullCache').lstrip().rstrip()

app.config["CACHE_DIR"] = environ.get("CACHE_DIR", "ruqquscache")

# Redis configs
app.config["CACHE_REDIS_URL"] = environ.get("REDIS_URL","").rstrip().lstrip()
app.config["CACHE_DEFAULT_TIMEOUT"] = 60
app.config["CACHE_KEY_PREFIX"] = "flask_caching_"
app.config["REDIS_POOL_SIZE"]=int(environ.get("REDIS_POOL_SIZE", 3))

# AWS configs
app.config["S3_BUCKET"]=environ.get("S3_BUCKET_NAME","").lstrip().rstrip()

redispool=ConnectionPool(
    max_connections=app.config["REDIS_POOL_SIZE"],
    host=app.config["CACHE_REDIS_URL"].split("://")[1]
    ) if app.config["CACHE_TYPE"]=="redis" else None
app.config["CACHE_OPTIONS"]={'connection_pool':redispool} if app.config["CACHE_TYPE"]=="redis" else {}

app.config["READ_ONLY"]=bool(int(environ.get("READ_ONLY", False)))

app.config["DEBUG"]=bool(int(environ.get("DEBUG", 0)))

#precompute logo urls
app.config["IMG_URL_LOGO_WHITE"] = f"/logo/white/{app.config['COLOR_PRIMARY'].lower()}/{app.config['SITE_NAME'][0].lower()}"
app.config["IMG_URL_LOGO_MAIN"] = f"/logo/main/{app.config['COLOR_PRIMARY'].lower()}/{app.config['SITE_NAME'][0].lower()}"
app.config["IMG_URL_JUMBOTRON"] = f"/logo/jumbotron/{app.config['COLOR_PRIMARY'].lower()}/{app.config['SITE_NAME'][0].lower()}"
app.config["IMG_URL_FAVICON"]=f"/logo/splash/{app.config['COLOR_PRIMARY']}/{app.config['SITE_NAME'][0].lower()}/64/64"
app.config["IMG_URL_THUMBSPLASH"]=f"/logo/splash/{app.config['COLOR_PRIMARY']}/{app.config['SITE_NAME'][0].lower()}/1200/630"

#Cloudflare Turnstile
app.config["CLOUDFLARE_TURNSTILE_KEY"]=environ.get("CLOUDFLARE_TURNSTILE_KEY",'').lstrip().rstrip()
app.config["CLOUDFLARE_TURNSTILE_SECRET"]=environ.get("CLOUDFLARE_TURNSTILE_SECRET",'').lstrip().rstrip()

Markdown(app)
cache = Cache(app)

if bool(int(environ.get("MINIFY",0))):
    Minify(app)

# app.config["CACHE_REDIS_URL"]
app.config["RATELIMIT_STORAGE_URI"] = environ.get("REDIS_URL", 'memory://').lstrip().rstrip()
app.config["RATELIMIT_KEY_PREFIX"] = "flask_limiting_"
app.config["RATELIMIT_ENABLED"] = not bool(int(environ.get("DISABLE_RATELIMIT", 0)))
app.config["RATELIMIT_DEFAULTS_DEDUCT_WHEN"]=lambda x:True
app.config["RATELIMIT_DEFAULTS_EXEMPT_WHEN"]=lambda:False
app.config["RATELIMIT_HEADERS_ENABLED"]=True

limiter = Limiter(
    lambda: request.remote_addr,
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

# import and bind all routing functions
import qually.classes
from qually.routes import *
import qually.helpers.jinja2
from qually.helpers.get import *

#purge css from cache
cache.delete_memoized(qually.routes.main_css)

# def drop_connection():

#     g.db.rollback()
#     g.db.close()
#     gevent.getcurrent().kill()


# enforce https
@app.before_request
def before_request():

    g.timestamp = int(time.time())
    g.nonce=generate_hash(f'{g.timestamp}+{session.get("session_id")}')
    g.db = db_session()

    if "session_id" not in session:
        session["session_id"] = token_hex(16)

    g.timestamp = int(time.time())

    g.db = db_session()
    # g.ip=None
    # g.ua=None
    # g.is_archive=False
    # g.is_tor=request.headers.get("cf-ipcountry")=="T1"

    # ip_ban= get_ip(request.remote_addr)

    # if ip_ban and ip_ban.unban_utc and ip_ban.unban_utc > g.timestamp:
    #     ip_ban.unban_utc = g.timestamp + 60*60
    #     g.db.add(ip_ban)
    #     g.db.commit()
    #     return jsonify({"error":"Your ban has been reset for another hour. Slow down."}), 429
    # elif ip_ban and "archive" in ip_ban.reason:
    #     g.ip=ip_ban
    #     g.is_archive=True
    # elif ip_ban and ip_ban.reason=="malicious scraper honeypot" and session.get("user_id"):
    #     pass

    # elif ip_ban:
    #     return jsonify({"error":"Refused due to your previous malicious conduct"}), 424

    session.permanent = True

    useragent=request.headers.get("User-Agent", "NoAgent")

    # ua_ban = g.db.query(
    #     syzitus.classes.Agent).filter(
    #         or_(
    #             syzitus.classes.Agent.kwd.in_(useragent.split()),
    #             syzitus.classes.Agent.kwd.ilike(useragent)
    #             )
    #         ).first()

    # if ua_ban and ua_ban.instaban:
    #     existing_ban=get_ip(request.remote_addr)
    #     if not existing_ban:
    #         new_ip=syzitus.classes.IP(
    #             addr=request.remote_addr,
    #             unban_utc=None,
    #             reason="archive instaban",
    #             banned_by=1
    #             )
    #         g.db.add(new_ip)
    #         try:
    #             g.db.commit()
    #         except IntegrityError:
    #             pass    
    # if ua_ban and "archive" in ua_ban.reason:
    #         g.db.ua=ua_ban
    #         g.is_archive=True
    # elif ua_ban and request.path != "/robots.txt":
    #     return ua_ban.mock, ua_ban.status_code

    if app.config["FORCE_HTTPS"] and request.url.startswith(
            "http://") and "localhost" not in app.config["SERVER_NAME"]:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url), 301

    if not session.get("session_id"):
        session["session_id"] = token_hex(16)

    #default user to none
    g.user=None


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

    if app.config["FORCE_HTTPS"]:
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