import re
import secrets

from flask import request, g, render_template, redirect, abort, session, jsonify, send_file, redirect, make_response, Response
from hmac import compare_digest
from sqlalchemy.sql import or_
from werkzeug.security import safe_join, generate_password_hash, check_password_hash

from qually.classes import *
from qually.helpers.get import *
from qually.helpers.languages import LANGUAGES
from qually.helpers.mail import send_mail
from qually.helpers.posttoast import toast, toast_redirect, toast_error
from qually.helpers.sanitize import txt, html
from qually.helpers.security import generate_hash, validate_hash, tokenify
from qually.helpers.wrappers import logged_in, not_logged_in, has_seat, is_admin, user_update_lock, org_update_lock, no_cors, no_sanctions, cf_cache, token_auth
import qually.helpers.aws as aws

try:
    from flask_babel import Babel, gettext as T, ngettext as N
except ModuleNotFoundError:
    pass

from qually.__main__ import app, debug, limiter, debug, cache