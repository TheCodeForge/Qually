from qually.helpers.route_imports import *
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    pass

@app.get("/NCMR-<number>")
@logged_in
def get_ncmr_number(number):

    ncmr = get_ncmr(number)
    
    return render_template("record.html", record=ncmr)

@app.post("/NCMR-<number>")
@has_seat
def post_ncmr_number(number):

    ncmr = get_ncmr(number)

    entries=ncmr._layout[ncmr._status]

    print(ncmr._metadata)
    return str(ncmr._metadata)

    for entry in entries:
        if entry['value'] in request.form:
            getattr(ncmr, entry['value'])
            break

    g.db.add(ncmr)

    log=NCMRLog(
        user_id=g.user.id,
        ncmr_id=ncmr.id,
        created_utc=g.time,
        key=key,
        value=value,
        created_ip=request.remote_addr
        )
    g.db.add(log)

    g.db.commit()

    return toast(_("Changes saved"), data={"new":value})

    
@app.get("/create_ncmr")
@has_seat
def get_create_ncmr():
    return render_template("create/ncmr.html")

@app.get("/ncmr")
def get_ncmr_records():

    return render_template("ncmrs.html")


@app.post("/ncmr")
@has_seat
@org_update_lock
def post_ncmr_record():

    ncmr=NCMR(
        owner_id=g.user.id,
        organization_id=g.user.organization.id,
        number=g.user.organization.next_ncmr_id,
        created_utc=g.time,
        item_number=txt(request.form.get("item_number")),
        lot_number=txt(request.form.get("lot_number")),
        quantity=txt(request.form.get("quantity"))
        )

    g.db.add(ncmr)
    g.db.flush()

    log = NCMRLog(
        ncmr_id=ncmr.id,
        created_utc=g.time,
        user_id=g.user.id,
        key="State",
        value="Open"
        )
    g.db.add(log)
    g.db.commit()

    return toast_redirect(ncmr.permalink)