import urllib
from qually.helpers.route_imports import *
from qually.helpers.timezones import TIMEZONES
from qually.helpers.languages import LANGUAGES
from .login import valid_email_regex
try:
    from flask_babel import gettext as _, force_locale
except ModuleNotFoundError:
    pass

@app.post("/settings/approvers")
def post_settings_approvers():

    if not g.user.is_doc_control:
        abort(403)

    if request.form.get("get_group"):
        group=g.user.organization.approver_groups.filter_by(id=int(request.form.get('get_group'), 36)).first()
        if group:
            return toast_redirect(group.permalink)
        else:
            return toast_redirect("/settings/approvers")

    elif request.form.get("new_group_name"):

        new_group=ChangeApproverGroup(
            organization_id=g.user.organization.id,
            name=txt(request.form.get("new_group_name"))
            )

        g.db.add(new_group)
        g.db.commit()

        return toast_redirect(new_group.permalink)

@app.post('/settings/approvers/<gid>')
def post_settings_approvers_gid(gid):

    group=g.user.organization.approver_groups.filter_by(id=base36decode(gid)).first()

    key, value, response, do_reload = group._edit_form()

    if not key:
        return toast_error(_("Unable to save changes"))

    if do_reload:
        return toast_redirect(group.permalink)

    g.db.commit()

    return toast(_("Changes saved"), data={"new":response})

@app.post("/settings/organization")
@is_admin
def post_settings_organization():


    if request.form.get("org_name"):

        if request.form.get("org_name")==g.user.organization.name:
            return toast_error(_("You didn't change anything!"))

        old_name=g.user.organization.name
        g.user.organization.name=txt(request.form.get("org_name"))
        g.db.add(g.user.organization)

        with force_locale(g.user.organization.lang):
            log=OrganizationAuditLog(
                user_id=g.user.id,
                organization_id=g.user.organization_id,
                key=_("Organization Name"),
                new_value=txt(request.form.get("org_name"))
                )
            g.db.add(log)

    if request.form.get("lang"):

        if request.form.get("lang") not in LANGUAGES.values():
            return toast_error(_("That language is not currently supported."))

        g.user.organization.lang=request.form.get("lang")
        g.db.add(g.user.organization)


        with force_locale(g.user.organization.lang):
            log=OrganizationAuditLog(
                user_id=g.user.id,
                organization_id=g.user.organization_id,
                key=_("Language"),
                new_value=request.form.get("lang")
                )
            g.db.add(log)

    if request.form.get("tz"):

        if request.form.get("tz") not in TIMEZONES:
            return toast_error(_("Invalid timezone"))

        g.user.organization.tz=request.form.get("tz")
        g.db.add(g.user.organization)

        with force_locale(g.user.organization.lang):
            log=OrganizationAuditLog(
                user_id=g.user.id,
                organization_id=g.user.organization_id,
                key=_("Timezone"),
                new_value=request.form.get("tz")
                )
            g.db.add(log)

    if request.form.get("color"):

        try:
            i=int(request.form.get('color'), 16)
        except:
            return toast_error("Color code must be valid RGB hex value")

        g.user.organization.color=request.form.get('color')
        g.db.add(g.user.organization)

        with force_locale(g.user.organization.lang):
            log=OrganizationAuditLog(
                user_id=g.user.id,
                organization_id=g.user.organization_id,
                key=_("Color"),
                new_value=request.form.get("color")
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
    
    with force_locale(g.user.organization.lang):
        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key=_("Require Two-Factor Authentication"),
            new_value=f"{g.user.organization.requires_otp}"
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

    with force_locale(g.user.organization.lang):
        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key=str(user),
            new_value=f"{_('License')}={user.has_license}"
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

    with force_locale(g.user.organization.lang):
        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key=str(user),
            new_value=f"{_('Enabled')}={user.is_active}"
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

    with force_locale(g.user.organization.lang):
        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key=str(user),
            new_value=f"{_('Admin')}={user.is_org_admin}"
            )

        g.db.add(log)

    g.db.commit()

    return toast(msg)

@app.post("/settings/directory/permissions/<uid>/<value>")
@is_admin
def post_settings_directory_permissions(uid, value):

    user=get_account(uid)

    #simultaneously limits to valid roles and also gets role name
    for role in ROLES:
        if value==role['value']:
            with force_locale(g.user.organization.lang):
                name=role['name']
            break
    else:
        abort(404)

    if not user.is_active:
        return toast_error(_("Deactivated users cannot be assigned roles."))

    if not getattr(user, value) and not user.has_license:
        return toast_error(_("Special roles require a full license."))

    #toggle
    setattr(user, value, not getattr(user, value))
    g.db.add(user)

    log=OrganizationAuditLog(
        user_id=g.user.id,
        organization_id=g.user.organization_id,
        key=str(user),
        new_value=f"{name} = {getattr(user, value)}"
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

    with force_locale(g.user.organization.lang):
        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key=_("License Count"),
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
    
    with force_locale(g.user.organization.lang):
        log=OrganizationAuditLog(
            user_id=g.user.id,
            organization_id=g.user.organization_id,
            key=_("Invitated"),
            new_value=email
            )

        g.db.add(log)
    g.db.commit()
    
    return toast(_("Invitation sent to {email}").format(email=email))
        
        
@app.post('/settings/organization/prefix')
def post_settings_org_prefix():

    name=[x for x in request.form if x.endswith("_prefix")][0]

    kind=name.split("_")[0]
    print(kind)

    if kind not in ALL_PROCESSES:
        abort(404)

    reserved=list(
        [ALL_PROCESSES[x]._name.lower() for x in ALL_PROCESSES]
    )

    for x in ALL_PROCESSES:
        if getattr(g.user.organization, f'{x.lower()}_prefix', None):
            reserved.append(getattr(g.user.organization, f'{x.lower()}_prefix').lower())

    new_prefix=request.form.get(name)

    if new_prefix.lower() in reserved and new_prefix.lower() != ALL_PROCESSES[request.form['kind']]._name.lower():
        return toast_error(_("Prefix {x} already in use").format(x=new_prefix))

    setattr(g.user.organization, f"{ALL_PROCESSES[kind]._name.lower()}_prefix", new_prefix)
    g.db.add(g.user.organization)
    g.db.commit()

    return toast(_("Changes saved"))
