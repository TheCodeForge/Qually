from qually.helpers.route_imports import *

@app.get("/NCMR-<number>")
@logged_in
def get_ncmr_number(number):

    ncmr = get_ncmr(number)
    
    return render_template("ncmr.html", ncmr=ncmr)

    
