from qually.helpers.route_imports import *
try:
    from flask_babel import gettext as _, force_locale
except ModuleNotFoundError:
    pass

VALID_KINDS={
    'ncmr':NCMR,
    'capa':CAPA
}

@app.get("/<kind>-<number>")
@logged_in
def get_record_number(kind, number):

    record = get_record(kind, number)
    
    return render_template("record.html", record=record)

@app.post("/<kind>-<number>")
@has_seat
def post_record_number(kind, number):

    record = get_record(kind, number)

    with force_locale(g.user.organization.lang):
        entries=record._layout[record._status]

    for entry in entries:
        if entry['value'] in request.form:
            if entry['kind']=='multi':
                setattr(record, entry['raw'], request.form[entry['value']])
                setattr(record, entry['value'], html(request.form[entry['value']]))
                key=entry['name']
                value=txt(request.form[entry['value']])
                response=getattr(record, entry['value'])
            elif entry['kind']=='dropdown':
                setattr(record, entry['value'], int(request.form[entry['value']]))
                key=entry['name']
                value=entry['values'].get(int(request.form[entry['value']]))
                response=value
            elif entry['kind']=='user':
                n=request.form.get(entry['value'])
                if n:
                    setattr(record, entry['value'], int(request.form[entry['value']]))
                    value=getattr(record, entry['relationship']).name
                else:
                    setattr(record, entry['value'], None)
                    value=""
                key=entry['name']
                response=value
            else:
                setattr(record, entry['value'], txt(request.form[entry['value']]))
                key=entry['name']
                value=getattr(record, entry['value'])
                response=value

            break
    else:
        return toast_error(_("Unable to save changes"))

    g.db.add(record)

    #clear any existing approvals on phase and log clearing

    approvals_cleared = g.db.query(eval(record._approval_class)).filter_by(record_id=record.id, status_id=record._status).delete()
    if approvals_cleared:

        with force_locale(g.user.organization.lang):
            appr_clear_log=eval(record._log_class)(
                user_id=g.user.id,
                record_id=record.id,
                created_utc=g.time,
                key=f"{_('Approvals')} - {record.status}",
                value=_("Cleared"),
                created_ip=request.remote_addr
                )
            g.db.add(appr_clear_log)


    log=eval(record._log_class)(
        user_id=g.user.id,
        record_id=record.id,
        created_utc=g.time,
        key=key,
        value=value,
        created_ip=request.remote_addr
        )
    g.db.add(log)

    g.db.commit()

    return toast(_("Changes saved"), data={"new":response})

@app.post("/<kind>-<number>/status")
@has_seat
def post_record_number_status(kind, number):

    record = get_record(kind, number)

    transition = [x for x in record._transitions[record._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    if g.user not in transition['users']:
        return toast_error(_("You are not authorized to do that."), 403)

    if transition.get("approval"):
        return toast_error(_("This transition requires approval signatures."), 403)

    if transition['to']<100 and (not record._lifecycle[transition['to']]['users'] or not record._lifecycle[transition['to']]['users'][0]):
        return toast_error(_("A user must be assigned to the {x} phase first.").format(x=record._lifecycle[transition['to']]['name']), 409)


    #transition is approved by system, update record and log

    record._status=transition['to']
    g.db.add(record)

    with force_locale(g.user.organization.lang):
        log=eval(record._log_class)(
            user_id=g.user.id,
            record_id=record.id,
            created_utc=g.time,
            key=_("Status"),
            value=record.status,
            created_ip=request.remote_addr
            )

    g.db.add(log)

    g.db.commit()

    return toast_redirect(record.permalink)

@app.post("/<kind>-<number>/approve")
@has_seat
def post_record_number_approve(kind, number):

    record = get_record(kind, number)

    transition = [x for x in record._transitions[record._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    if g.user not in transition['users']:
        return toast_error(_("You are not authorized to do that."), 403)

    if record.has_approved:
        return toast_error(_("You already approved this."))

    if transition['to']<100 and (not record._lifecycle[transition['to']]['users'] or not record._lifecycle[transition['to']]['users'][0]):
        return toast_error(_("A user must be assigned to the {x} phase first.").format(x=record._lifecycle[transition['to']]['name']), 409)

    ## Validate password
    if not check_password_hash(g.user.passhash, request.form.get("password")):
        return toast_error(_("Incorrect password"), 403)

    if not transition.get("approval"):
        return toast_error(_("This transition does not require approval signatures."), 403)

    #approval is approved by system, update data log

    with force_locale(g.user.organization.lang):
        appr_log=eval(record._log_class)(
            user_id=g.user.id,
            record_id=record.id,
            created_utc=g.time,
            key=f"{_('Approvals')} - {record.status}",
            value=_("Approved"),
            created_ip=request.remote_addr
            )
        g.db.add(appr_log)

    approval=eval(record._approval_class)(
        user_id=g.user.id,
        record_id=record.id,
        status_id=record._status,
        created_utc=g.time
        )
    g.db.add(approval)

    g.db.flush()
    
    #refresh record and get number of apprs
    #if all have approved, advance phase
    g.db.refresh(record)
    if len(record.phase_approvals(record._status)) >= len(transition['users']):
        record._status=transition['to']
        g.db.add(record)
        log=eval(record._log_class)(
            user_id=g.user.id,
            record_id=record.id,
            created_utc=g.time,
            key=_("Status"),
            value=record.status,
            created_ip=request.remote_addr
            )

        g.db.add(log)


    g.db.commit()

    return toast_redirect(record.permalink)

@app.post("/<kind>-<number>/unapprove")
@logged_in
def post_record_number_unapprove(kind, number):

    record = get_record(kind, number)

    transition = [x for x in record._transitions[record._status] if x['id']==request.form.get('transition_id')]

    try:
        transition=transition[0]
    except IndexError:
        return toast_error(_("This record has changed status. Please reload this page."), 403)

    approvals = [x for x in record.approvals if x.user_id==g.user.id and x.status_id==record._status]

    if not approvals:
        return toast_error(_("You don't have any approvals to clear."))

    for approval in approvals:
        g.db.delete(approval)
    g.db.flush()

    with force_locale(g.user.organization.lang):
        appr_log=eval(record._log_class)(
            user_id=g.user.id,
            record_id=record.id,
            created_utc=g.time,
            key=f"{_('Approvals')} - {record.status}",
            value=_("Unapproved"),
            created_ip=request.remote_addr
            )
        g.db.add(appr_log)

    g.db.commit()

    return toast_redirect(record.permalink)

    
@app.get("/create_<kind>")
@has_seat
def get_create_record(kind):

    kind=request.path.split('_')[1]

    if kind not in VALID_KINDS:
        abort(404)

    OBJ=VALID_KINDS[kind]

    return render_template(f"create_record.html", obj=OBJ)

@app.get("/ncmr")
def get_record_records():

    kind=request.path.lstrip('/')

    if kind not in VALID_KINDS:
        abort(404)

    return render_template(f"{kind}s.html")


@app.post("/ncmr")
@has_seat
@org_update_lock
def post_record_record():

    kind=request.path.lstrip('/')
    if kind not in VALID_KINDS:
        abort(404)

    OBJ = VALID_KINDS[kind]

    record=OBJ(
        owner_id=g.user.id,
        organization_id=g.user.organization.id,
        number=getattr(g.user.organization, f"next_{kind}_id"),
        created_utc=g.time
        )

    g.db.add(record)
    g.db.flush()

    with force_locale(g.user.organization.lang):
        entries=record._layout[0]

    for entry in entries:
        if entry['value'] in request.form:
            if entry['kind']=='multi':
                setattr(record, entry['raw'], request.form[entry['value']])
                setattr(record, entry['value'], html(request.form[entry['value']]))
            elif entry['kind']=='dropdown':
                setattr(record, entry['value'], int(request.form[entry['value']]))
            elif entry['kind']=='user':
                n=request.form.get(entry['value'])
                if n:
                    setattr(record, entry['value'], int(request.form[entry['value']]))
                else:
                    setattr(record, entry['value'], None)
            else:
                setattr(record, entry['value'], txt(request.form[entry['value']]))

    g.db.add(record)
    g.db.flush()

    log = eval(record._log_class)(
        record_id=record.id,
        created_utc=g.time,
        user_id=g.user.id,
        key="State",
        value="Open"
        )
    g.db.add(log)
    g.db.commit()

    return toast_redirect(record.permalink)