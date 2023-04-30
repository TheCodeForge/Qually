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
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key="Organization Name",
            old_value=old_name,
            new_value=request.form.get("org_name")
            )
        g.db.add(log)

    g.db.commit()

    return toast("Organization settings saved!")

@app.post("/settings/directory/toggle_license/<uid>")
@is_admin
def post_settings_directory_toggle_license_uid(uid):

    user=get_account(uid)

    if user.has_license:

        if user.is_org_admin:
            return toast_error("Administrators must have an assigned license.")

        msg=f"License removed from {user.name}"

        user.has_license=False

        g.db.add(user)

    else:

        if not user.is_active:
            return toast_error("You can't assign a license to deactivated users.")

        if g.time > g.user.organization.license_expire_utc:
            return toast_error("Your organization licenses have expired.")

        if g.user.organization.licenses_used >= g.user.organization.license_count:
            return toast_error("Your organization has reached its purchased license count.")

        msg=f"License assigned to {user.name}"

        user.has_license = True
        g.db.add(user)
        g.db.flush()

        if g.user.organization.licenses_used >= g.user.organization.license_count:
            g.db.rollback()
            return toast_error("Your organization has reached its purchased license count.")

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
        old_value=f"License={not user.has_license}",
        new_value=f"License={user.has_license}"
        )
    g.db.add(log)

    g.db.commit()

    return toast(msg)

@app.post("/settings/directory/toggle_enable/<uid>")
@is_admin
def post_settings_directory_toggle_enable_uid(uid):

    user=get_account(uid)

    if user.is_active:

        if user.is_org_admin:
            return toast_error("Administrator accounts may not be deactivated.")

        if user.has_license:
            return toast_error("Take away their assigned license first")

        msg=f"{user.name} user account deactivated"

    else:

        msg=f"{user.name} user account activated"

    user.is_active = not user.is_active
    user.has_license = user.is_active and user.has_license
    g.db.add(user)

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
        old_value=f"Enabled={not user.is_active}",
        new_value=f"Enabled={user.is_active}"
        )

    g.db.add(log)
    g.db.commit()

    return toast(msg)

@app.post("/settings/directory/toggle_admin/<uid>")
@is_admin
def post_settings_directory_toggle_admin_uid(uid):

    user=get_account(uid)

    if user.is_org_admin:

        if user.id==g.user.id:
            return toast_error("You cannot remove your own administrator status.")

        msg=f"Administrator status removed from {user.name}"

    else:

        if not user.is_active:
            return toast_error("Administrators require a full license.")

        if not user.has_license:
            return toast_error("Administrators require a full license.")

        msg=f"Administrator status granted to {user.name}"

    user.is_org_admin = not user.is_org_admin
    g.db.add(user)

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
        old_value=f"Admin={not user.is_active}",
        new_value=f"Admin={user.is_active}"
        )

    g.db.add(log)

    g.db.commit()

    return toast(msg)