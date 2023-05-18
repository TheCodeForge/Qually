from qually.helpers.route_imports import *
try:
    from flask_babel import gettext as _, force_locale
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

    with force_locale(g.user.organization.lang):
        entries=ncmr._layout[ncmr._status]

    for entry in entries:
        if entry['value'] in request.form:
            if entry['kind']=='multi':
                setattr(ncmr, entry['raw'], request.form[entry['value']])
                setattr(ncmr, entry['value'], html(request.form[entry['value']]))
                key=entry['name']
                value=txt(request.form[entry['value']])
                response=getattr(ncmr, entry['value'])
            elif entry['kind']=='dropdown':
                setattr(ncmr, entry['value'], int(request.form[entry['value']]))
                key=entry['name']
                value=entry['values'].get(int(request.form[entry['value']]))
                response=value
            elif entry['kind']=='user':
                setattr(ncmr, entry['value'], int(request.form[entry['value']]))
                key=entry['name']
                value=getattr(ncmr, entry['relationship']).name
                response=value
            else:
                setattr(ncmr, entry['value'], txt(request.form[entry['value']]))
                key=entry['name']
                value=getattr(ncmr, entry['value'])
                response=value

            break
    else:
        return toast_error(_("Unable to save changes"))

    g.db.add(ncmr)

    #clear any existing approvals on phase and log clearing

    approvals_cleared = g.db.query(NCMRApproval).filter_by(ncmr_id=ncmr.id, status_id=ncmr._status).delete()
    if approvals_cleared:

        with force_locale(g.user.organization.lang):
            appr_clear_log=NCMRLog(
                user_id=g.user.id,
                ncmr_id=ncmr.id,
                created_utc=g.time,
                key=f"{_('Approvals')} - {ncmr.status}",
                value=_("Cleared"),
                created_ip=request.remote_addr
                )
            g.db.add(appr_clear_log)


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

    return toast(_("Changes saved"), data={"new":response})

@app.post("/NCMR-<number>/status")
@has_seat
def post_ncmr_number_status(number):

    ncmr=get_ncmr(number)

    transition = [x for x in ncmr._transitions[ncmr._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    if g.user not in transition['users']:
        return toast_error(_("You are not authorized to do that."), 403)

    if transition.get("approval"):
        return toast_error(_("This transition requires approval signatures."), 403)

    if transition['to']<100 and not ncmr._lifecycle[transition['to']]['users']:
        return toast_error(_("You must assign a user to the {x} phase first.").format(x=ncmr._lifecycle[transition['to']]['name']), 409)


    #transition is approved by system, update record and log

    ncmr._status=transition['to']
    g.db.add(ncmr)

    with force_locale(g.user.organization.lang):
        log=NCMRLog(
            user_id=g.user.id,
            ncmr_id=ncmr.id,
            created_utc=g.time,
            key=_("Status"),
            value=ncmr.status,
            created_ip=request.remote_addr
            )

    g.db.add(log)

    g.db.commit()

    return toast_redirect(ncmr.permalink)

@app.post("/NCMR-<number>/approve")
@has_seat
def post_ncmr_number_approve(number):

    ncmr=get_ncmr(number)

    transition = [x for x in ncmr._transitions[ncmr._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    if g.user not in transition['users']:
        return toast_error(_("You are not authorized to do that."), 403)

    if ncmr.has_approved:
        return toast_error(_("You already approved this."))

    if transition['to']<100 and not ncmr._lifecycle[transition['to']]['users']:
        return toast_error(_("You must assign a user to the {x} phase first.").format(x=ncmr._lifecycle[transition['to']]['name']), 409)

    ## Validate password
    if not check_password_hash(g.user.passhash, request.form.get("password")):
        return toast_error(_("Incorrect password"), 403)

    if not transition.get("approval"):
        return toast_error(_("This transition does not require approval signatures."), 403)

    #approval is approved by system, update data log

    with force_locale(g.user.organization.lang):
        appr_log=NCMRLog(
            user_id=g.user.id,
            ncmr_id=ncmr.id,
            created_utc=g.time,
            key=f"{_('Approvals')} - {ncmr.status}",
            value=_("Approved"),
            created_ip=request.remote_addr
            )
        g.db.add(appr_log)

    approval=NCMRApproval(
        user_id=g.user.id,
        ncmr_id=ncmr.id,
        status_id=ncmr._status,
        created_utc=g.time
        )
    g.db.add(approval)

    g.db.flush()
    
    #refresh ncmr and get number of apprs
    #if all have approved, advance phase
    g.db.refresh(ncmr)
    if len(ncmr.phase_approvals(ncmr._status)) >= len(transition['users']):
        ncmr._status=transition['to']
        g.db.add(ncmr)
        log=NCMRLog(
            user_id=g.user.id,
            ncmr_id=ncmr.id,
            created_utc=g.time,
            key=_("Status"),
            value=ncmr.status,
            created_ip=request.remote_addr
            )

        g.db.add(log)


    g.db.commit()

    return toast_redirect(ncmr.permalink)

@app.post("/NCMR-<number>/unapprove")
@logged_in
def post_ncmr_number_unapprove(number):

    ncmr=get_ncmr(number)

    transition = [x for x in ncmr._transitions[ncmr._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    approvals = [x for x in ncmr.approvals if x.user_id==g.user.id and x.status_id==ncmr._status]

    if not approvals:
        return toast_error(_("You don't have any approvals to clear."))

    for approval in approvals:
        g.db.delete(approval)
    g.db.flush()

    with force_locale(g.user.organization.lang):
        appr_log=NCMRLog(
            user_id=g.user.id,
            ncmr_id=ncmr.id,
            created_utc=g.time,
            key=f"{_('Approvals')} - {ncmr.status}",
            value=_("Unapproved"),
            created_ip=request.remote_addr
            )
        g.db.add(appr_log)

    g.db.commit()

    return toast_redirect(ncmr.permalink)



    
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