from qually.helpers.route_imports import *
from flask_babel import gettext as _, ngettext as N_

@app.errorhandler(401)
def error_401(e):
  
  return redirect('/sign_in')
