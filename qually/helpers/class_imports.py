import time

from flask import g, abort, session, request
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import deferred, relationship

from qually.helpers.lazy import lazy
from qually.helpers.base36 import base36encode, base36decode
from qually.helpers.security import generate_hash, validate_hash

from qually.classes.mixins import core_mixin

from qually.__main__ import Base, cache, app, debug