from qually.helpers.route_imports import *

@app.get("/settings/profile")
@app.get("/settings/security")
@app.get("/settings/organization")
@app.get("/settings/directory")
@logged_in
def get_settings_profile():

    page=request.path.split("/")[2]
    return render_template(f"settings/{page}.html")

@app.get("/settings/audit")
@app.get("/settings/audit/<log_id>")
@is_admin
def get_settings_audit(log_id=None):

    page=int(request.args.get("page", 1))

    listing=g.user.organization.logs

    if log_id:
        listing=listing.filter_by(id=base36decode(log_id))

    listing=listing.order_by(OrganizationAuditLog.id.desc()).offset(100*(page-1)).limit(100).all()

    return render_template(
        f"settings/audit.html",
        listing=listing)

@app.post("/settings/organization")
@is_admin
def post_settings_organization():


    if request.form.get("org_name"):

        if request.form.get("org_name")==g.user.organization.name:
            return toast_error("You didn't change anything!")

        old_name=g.user.organization.name
        g.user.organization.name=request.form.get("org_name")
        g.db.add(g.user.organization)

        log=OrganizationAuditLog(
            key="Name",
            old_value=old_name,
            new_value=request.form.get("org_name")
            )
        g.db.add(log)

    g.db.commit()

    return toast("Organization settings saved!")