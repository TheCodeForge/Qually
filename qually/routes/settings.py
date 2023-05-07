from qually.helpers.route_imports import *

@app.get("/settings/profile")
@app.get("/settings/security")
@app.get("/settings/directory")
@logged_in
def get_settings_profile():

    page=request.path.split("/")[2]
    return render_template(f"settings/{page}.html")

@app.get("/settings/organization")
@app.get("/settings/plan")
@is_admin
def get_settings_admin():

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

@app.post("/settings/security/password")
@logged_in
def post_settings_security_password():

    if not check_password_hash(g.user.passhash, request.form.get("password")):
        return toast_error("Invalid password")

    if request.form.get("new_password") != request.form.get("confirm_password"):
        return toast_error("Passwords do not match")

    g.user.passhash = generate_password_hash(request.form.get("new_password"))
    g.db.add(g.user)
    g.db.commit()

    return toast("Password changed")


@app.post("/settings/security/remove_otp")
@logged_in
def post_settings_security_remove_otp():

    if not check_password_hash(g.user.passhash, request.form.get("password")):
        return toast_error("Invalid password")

    if not g.user.validate_otp(request.form.get("otp_code"), allow_reset=True):
        return toast_error("Invalid two-factor code")

    g.user.otp_secret=None
    g.db.add(g.user)
    g.db.commit()

    if g.user.organization.requires_otp:
        return toast_redirect("/set_otp")

    return toast("Two-Factor Code Removed")

@app.post("/settings/profile/avatar")
@logged_in
def post_settings_profile_avatar():

    if request.files.get("profile"):
        g.user.set_profile(request.files["profile"])
    else:
        g.user.del_profile()

    return toast_redirect("/settings/profile")

@app.post("/settings/profile")
def post_settings_profile():

    if request.form.get("title"):
        g.user.title=request.form.get("title")

    if request.form.get("lang"):
        self.lang = request.form.get("lang")

    g.db.add(g.user)
    g.db.commit()

    return toast(_("Settings saved"))