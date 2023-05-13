from qually.helpers.route_imports import *

@app.get("/NCMR-<number>")
@logged_in
def get_ncmr_number(number):

    ncmr = get_ncmr(number)
    
    return render_template("ncmr.html", ncmr=ncmr)

    
@app.get("/create_ncmr")
@has_seat
def get_create_ncmr():
    return render_template("create/ncmr.html")

@app.post("/ncmr")
@has_seat
def post_create_ncmr():

    ncmr=NCMR(
        owner_id=g.user.id,
        organization_id=g.user.organization.id,
        number=g.user.organization.next_ncmr_id
        )

    g.db.add(ncmr)
    g.db.commit()
    return toast_redirect(ncmr.permalink)