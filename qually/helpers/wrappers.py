from flask import g, session, abort, render_template, jsonify, request, make_response, Response
from os import environ
from werkzeug.wrappers.response import Response as RespObj
from random import randint

from .security import validate_hash
from .posttoast import *

from qually.classes import User
from qually.__main__ import Base, app, g, debug


# Wrappers
def logged_in(f):
    # decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if not g.user:
            abort(401)

        if not g.user.is_active:
            abort(403)

        resp = make_response(f(*args, **kwargs))

        resp.headers.add("Cache-Control", "private")
        resp.headers.add(
            "Access-Control-Allow-Origin",
            app.config["SERVER_NAME"])
        return resp

    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper



def not_logged_in(f):
    # decorator for any view that requires not being logged in (ex. signup)

    def wrapper(*args, **kwargs):

        if g.user:
            return redirect("/")

        resp = make_response(f(*args, **kwargs))

        resp.headers.add("Cache-Control", "private")
        resp.headers.add(
            "Access-Control-Allow-Origin",
            app.config["SERVER_NAME"])
        return resp

    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper

def has_seat(f):
    # decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if not g.user:
            abort(401)

        if not g.user.is_active:
            abort(403)

        if not g.user.has_license:
            abort(401)

        if g.user.organization.license_expire_utc < g.timestamp:
            abort(402)

        resp = make_response(f(*args, **kwargs))

        resp.headers.add("Cache-Control", "private")
        resp.headers.add(
            "Access-Control-Allow-Origin",
            app.config["SERVER_NAME"])
        return resp

    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper

def is_admin(f):
    # decorator for any view that requires login (ex. settings)

    def wrapper(*args, **kwargs):

        if not g.user:
            abort(401)

        if not g.user.is_active:
            abort(403)

        if not g.user.is_org_admin:
            abort(403)

        resp = make_response(f(*args, **kwargs))

        resp.headers.add("Cache-Control", "private")
        resp.headers.add(
            "Access-Control-Allow-Origin",
            app.config["SERVER_NAME"])
        return resp

    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper


def user_update_lock(f):

    def wrapper(*args, **kwargs):

        #use below authentication to make user be with for update
        g.user = g.db.query(User).with_for_update().options(lazyload('*')).filter_by(id=g.user.id).first()

        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    wrapper.__doc__=f.__doc__
    return wrapper


def no_cors(f):
    """
    Decorator prevents content being iframe'd
    """

    def wrapper(*args, **kwargs):

        origin = request.headers.get("Origin", None)

        if origin and origin != "https://" + app.config["SERVER_NAME"] and app.config["FORCE_HTTPS"]==1:

            return "This page may not be embedded in other webpages.", 403

        resp = make_response(f(*args, **kwargs))
        resp.headers.add("Access-Control-Allow-Origin",
                         app.config["SERVER_NAME"]
                         )

        return resp

    wrapper.__name__ = f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper

# wrapper for api-related things that discriminates between an api url
# and an html url for the same content
# f should return {'api':lambda:some_func(), 'html':lambda:other_func()}


# def api(*scopes, no_ban=False):

#     def wrapper_maker(f):

#         def wrapper(*args, **kwargs):

#             if request.path.startswith('/api/v2'):

#                 if g.client:

#                     if not g.user or not g.client:
#                         return jsonify(
#                             {"error": "401 Not Authorized. Invalid or Expired Token"}), 401

#                     kwargs.pop('c')

#                     # validate app associated with token
#                     if client.application.is_banned:
#                         return jsonify({"error": f"403 Forbidden. The application `{client.application.app_name}` is suspended."}), 403

#                     # validate correct scopes for request
#                     for scope in scopes:
#                         if not client.__dict__.get(f"scope_{scope}"):
#                             return jsonify({"error": f"401 Not Authorized. Scope `{scope}` is required."}), 403

#                     if (request.method == "POST" or no_ban) and g.user.is_suspended:
#                         return jsonify({"error": f"403 Forbidden. The user account is suspended."}), 403

#                 if not g.user:
#                     return jsonify({"error": f"401 Not Authorized. You must log in."}), 401

#                 if g.user.is_suspended:
#                     return jsonify({"error": f"403 Forbidden. You are banned."}), 403
                    

#                 result = f(*args, **kwargs)

#                 if isinstance(result, dict):
#                     try:
#                         resp = result['api']()
#                     except KeyError:
#                         resp=result
#                 else:
#                     resp = result

#                 if not isinstance(resp, RespObj):
#                     resp = make_response(resp)

#                 resp.headers.add("Cache-Control", "private")
#                 resp.headers.add(
#                     "Access-Control-Allow-Origin",
#                     app.config["SERVER_NAME"])
#                 return resp

#             else:

#                 result = f(*args, **kwargs)

#                 if not isinstance(result, dict):
#                     return result

#                 try:
#                     if request.path.startswith('/inpage/'):
#                         return result['inpage']()
#                     elif request.path.startswith(('/api/vue/','/test/')):
#                         return result['api']()
#                     else:
#                         return result['html']()
#                 except KeyError:
#                     return result

#         wrapper.__name__ = f.__name__
#         wrapper.__doc__ = f"<small>oauth scopes: <code>{', '.join(scopes)}</code></small><br>{f.__doc__}" if scopes else f.__doc__
#         return wrapper

#     return wrapper_maker


SANCTIONS=[
    "CU",   #Cuba
    "IR",   #Iran
    "KP",   #North Korea
    "VE",   #Venezuela
]

def no_sanctions(f):

    def wrapper(*args, **kwargs):

        if request.headers.get("cf-ipcountry","") in SANCTIONS:
            abort(451)

        return f(*args, **kwargs)

    wrapper.__name__=f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper

def cf_cache(f):

    #Tell cloudflare that it can cache the resource

    def wrapper(*args, **kwargs):

        resp = f(*args, **kwargs)

        if not isinstance(resp, Response):
            resp=make_response(resp)

        if not g.user:
            resp.headers.add("Cache-Control", "public, max-age=2592000, s-maxage=2592000")

        return resp

    wrapper.__name__=f.__name__
    wrapper.__doc__ = f.__doc__
    return wrapper
