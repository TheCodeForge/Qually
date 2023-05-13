from qually.helpers.route_imports import *

@app.get("/NCMR-<number>")
@logged_in
def get_ncmr_number(number):

    ncmr = g.user.organization.ncmrs.filter_by(number=int(number)).first()

    