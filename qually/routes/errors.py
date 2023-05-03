from qually.helpers.route_imports import *

@app.errorhandler(401)
def error_401(e):
  
  return redirect('/sign_in')
