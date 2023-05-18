import urllib
from qually.helpers.route_imports import *
from qually.helpers.timezones import TIMEZONES
from qually.helpers.languages import LANGUAGES
from .login import valid_email_regex
try:
    from flask_babel import gettext as _
except ModuleNotFoundError:
    pass

@app.post("/settings/organization")
@is_admin
def post_settings_organization():


    if request.form.get("org_name"):

        if request.form.get("org_name")==g.user.organization.name:
            return toast_error(_("You didn't change anything!"))

        old_name=g.user.organization.name
        g.user.organization.name=txt(request.form.get("org_name"))
        g.db.add(g.user.organization)

        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key="Organization Name",
            new_value=txt(request.form.get("org_name"))
            )
        g.db.add(log)

    if request.form.get("lang"):

        if request.form.get("lang") not in LANGUAGES.values():
            return toast_error(_("That language is not currently supported."))

        g.user.organization.lang=request.form.get("lang")
        g.db.add(g.user.organization)

        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key="Language",
            new_value=request.form.get("lang")
            )
        g.db.add(log)

    if request.form.get("tz"):

        if request.form.get("tz") not in TIMEZONES:
            return toast_error(_("Invalid timezone"))

        g.user.organization.tz=request.form.get("tz")
        g.db.add(g.user.organization)

        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key="Timezone",
            new_value=request.form.get("tz")
            )
        g.db.add(log)

    g.db.commit()

    return toast("Changes saved")

@app.post("/settings/organization/toggle_otp")
@is_admin
def post_settings_directory_toggle_otp():
    
    if not g.user.organization.requires_otp and not g.user.otp_secret:
        return toast_error(_("Enable two-factor authentication on your own account first."))
    
    g.user.organization.requires_otp = not g.user.organization.requires_otp
    g.db.add(g.user.organization)
    
    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key="Organization",
        new_value=f"Require2FA={g.user.organization.requires_otp}"
        )
    g.db.add(log)
    
    g.db.commit()
    return toast(_("Settings saved"))

@app.post("/settings/directory/toggle_license/<uid>")
@is_admin
def post_settings_directory_toggle_license_uid(uid):

    user=get_account(uid)

    if user.has_license:

        if user.is_org_admin:
            return toast_error(_("Administrators must have an assigned license."))

        if g.time - user.license_assigned_utc < 60*60*24*7:
            return toast_error(_("There is a {n} day cooldown to unassign licenses.").format(n=7))

        msg=f"License removed from {user.name}"

        user.has_license=False

        g.db.add(user)

    else:

        if not user.is_active:
            return toast_error(_("You can't assign a license to deactivated users."))

        if g.time > g.user.organization.license_expire_utc:
            return toast_error(_("Your organization licenses have expired."))

        if g.user.organization.licenses_used >= g.user.organization.license_count:
            return toast_error(_("Your organization has reached its purchased license count."))

        msg=f"License assigned to {user.name}"

        user.has_license = True
        user.license_assigned_utc=g.time
        g.db.add(user)
        g.db.flush()

        if g.user.organization.licenses_used > g.user.organization.license_count:
            g.db.rollback()
            return toast_error(_("Your organization has reached its purchased license count."))

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
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
            return toast_error(_("Administrator accounts may not be deactivated."))

        # if user.has_license:
        #     return toast_error("Take away their assigned license first")

        msg=_("{name} user account deactivated").format(name=user.name)

    else:

        msg=_("{name} user account activated").format(name=user.name)

    user.is_active = not user.is_active
    #user.has_license = user.is_active and user.has_license
    g.db.add(user)

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
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
            return toast_error(_("You cannot remove your own administrator status."))

        msg=_("Administrator status removed from {name}").format(name=user.name)

    else:

        if not user.is_active:
            return toast_error(_("Deactivated users cannot be administrators."))

        if not user.has_license:
            return toast_error(_("Administrators require a full license."))

        msg=_("Administrator status granted to {name}").format(name=user.name)

    user.is_org_admin = not user.is_org_admin
    g.db.add(user)

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
        new_value=f"Admin={user.is_org_admin}"
        )

    g.db.add(log)

    g.db.commit()

    return toast(msg)

@app.post("/settings/directory/select_permissions/<uid>")
@is_admin
def post_settings_directory_select_permissions_uid(uid):

    user=get_account(uid)

    new_role=int(request.form.get("special_role"))

    if new_role and not user.has_license:
        return toast_error(_("That role requires a full license."))

    if not user.is_active:
        return toast_error(_("Deactivated users cannot be assigned roles."))


    user.special_role=new_role
    g.db.add(user)

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
        new_value=_("Role")+"="+ROLES[new_role]
        )

    g.db.add(log)

    g.db.commit()

    return toast(_("Changes saved"))

@app.post("/settings/plan")
@is_admin
@org_update_lock
def post_settings_plan():

    new_seat_count = int(request.form.get("license_count", 0))

    if new_seat_count==g.user.organization.license_count and g.user.organization.license_expire_utc > g.time+60*60*24*365:
        return toast_error(_("You didn't change anything!"))
        
    if new_seat_count < g.user.organization.licenses_used:
        return toast_error(_("You can't reduce your organization license count below current usage."))

    if new_seat_count < g.user.organization.license_count and g.time < g.user.organization.licenses_last_increased_utc + 60*60*24*21:
        return toast_error(_("There is a {n} day cooldown after increasing license count before it may be decreased.").format(n=21))
        
    #compute remaining seatseconds
    seat_seconds = max(0, g.user.organization.license_count * (g.user.organization.license_expire_utc - g.time))
    
    #expiration timer
    new_expire_timer = seat_seconds // new_seat_count
    
    #if reducing seats or if new time > 1yr, adjust and save
    if new_seat_count < g.user.organization.license_count or new_expire_timer > 60*60*24*365:

        g.user.organization.license_count = new_seat_count
        g.user.organization.license_expire_utc += new_expire_timer

    else:

        desired_seat_seconds=new_seat_count*60*60*24*365
        buying_seat_seconds = desired_seat_seconds - seat_seconds
        price_cents = int(buying_seat_seconds/(60*60*24*365) * app.config["CENTS_PER_SEATYEAR"])

        # new_txn = PayPalTxn(
        #     user_id=g.user.id,
        #     created_utc=g.time,
        #     seat_count=new_seat_count,
        #     usd_cents=price_cents
        #     )

        # g.db.add(new_txn)
        # g.db.flush()

        # PayPalClient().create(new_txn)
        # g.db.add(new_txn)
        # g.db.commit()
        # return toast_redirect(new_txn.approve_url)
        return toast_error(f"Base: ${app.config['CENTS_PER_SEATYEAR'] * new_seat_count/100:.2f} | Prorated: ${price_cents/100:.2f}")

    g.db.add(g.user.organization)

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key="License Count",
        new_value=str(new_seat_count)
        )

    g.db.add(log)
    g.db.commit()

    return toast_redirect("/settings/plan")


@app.post("/settings/directory/invite")
@is_admin
def post_settings_directory_invite():

    email=request.form.get("email")

    if email.endswith("@gmail.com"):
        gmail_username=email.split('@')[0]
        gmail_username=gmail_username.split('+')[0]
        gmail_username=gmail_username.replace('.','')
        email=f"{gmail_username}@gmail.com"
        
    if not re.fullmatch(valid_email_regex, email):
        return toast_error(_("Invalid email address"))

    existing=get_account_by_email(email, graceful=True)
    if existing:
        return toast_error(_("That email is already in use."))

    data={
        "email":email,
        'name':request.form.get("name"),
        'organization_id':g.user.organization.base36id,
        't':g.time
    }
    
    link=f"https://{app.config['SERVER_NAME']}{tokenify('/accept_invite', data)}"
    
    send_mail(
        email,
        subject=_("You've been invited to join {orgname} on {sitename}").format(orgname=g.user.organization.name, sitename=app.config['SITE_NAME']),
        html=render_template(
            "mail/invite.html",
            link=link,
            subject=_("You've been invited to join {orgname} on {sitename}").format(orgname=g.user.organization.name, sitename=app.config['SITE_NAME'])
            )
        )
    
    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key="Directory",
        new_value=f"Invited <{email}>"
        )

    g.db.add(log)
    g.db.commit()
    
    return toast(_("Invitation sent to {email}").format(email=email))
        
        
