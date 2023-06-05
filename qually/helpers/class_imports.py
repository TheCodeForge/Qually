import time

from flask import g, abort, session, request
from sqlalchemy import Column, Integer, BigInteger, Float, String, Boolean, ForeignKey, Index, UniqueConstraint, text, or_, and_
from sqlalchemy.orm import deferred, relationship

from qually.helpers.base36 import base36encode, base36decode
from qually.helpers.languages import LANGUAGES, org_lang
from qually.helpers.lazy import lazy, tryer
from qually.helpers.roles import ROLES
from qually.helpers.sanitize import txt, html
from qually.helpers.security import generate_hash, validate_hash
import qually.helpers.aws as aws

from qually.classes.mixins import core_mixin, process_mixin, revisio

from qually.__main__ import Base, cache, app, debug


try:
    from flask_babel import Babel, gettext as T, ngettext as N
except ModuleNotFoundError:
    pass