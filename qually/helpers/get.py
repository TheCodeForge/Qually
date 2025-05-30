from .base36 import base36encode, base36decode

from flask import g, abort, request
# from sqlalchemy import *
# from sqlalchemy.orm import *

from qually.classes import *
from qually.classes.user import User

def get_account(b36uid, graceful=False):
    
    id=base36decode(b36uid)

    user=g.user.organization.users.filter_by(id=id).first()

    if not user and not graceful:
        abort(404)

    return user

def get_account_by_email(email, graceful=False):

    if email.endswith("@gmail.com"):
        gmail_username=email.split('@')[0]
        gmail_username=gmail_username.split('+')[0]
        gmail_username=gmail_username.replace('.','')
        email=f"{gmail_username}@gmail.com"

    email=email.replace("%", r"\%")
    email=email.replace("_", r"\_")

    #if logged in, pre-filter by org. Otherwise, don't pre-filter but return t/f
    if g.user:
        user=g.user.organization.users.filter(User.email.ilike(email)).first()

        if not user and not graceful:
            abort(404)

        return user
    else:
        user=g.db.query(User).filter(User.email.ilike(email)).first()

        if not user and not graceful:
            abort(404)

        if request.path=="/sign_in":
            return user
        else:
            return bool(user)


def get_record(kind, number, graceful=False):

    kind=kind.lower()
    if kind not in ['ncmr', "capa", "dvtn"]:
        abort(404)

    item = getattr(g.user.organization, f"{kind}s").filter_by(number=int(number))

    if request.method != "GET":
        item=item.with_for_update()

    item=item.first()

    if not item and not graceful:
        abort(404)

    return item