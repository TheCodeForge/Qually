from .base36 import base36encode, base36decode

from flask import g, abort
# from sqlalchemy import *
# from sqlalchemy.orm import *

from qually.classes import *

def get_account(b36uid, graceful=False):

    id=base36decode(b36uid)

    user=g.db.query(User).filter_by(id=id).first()

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

    user=g.db.query(User).filter(User.email.ilike(email)).first()

    if not user and not graceful:
        abort(404)

    return user